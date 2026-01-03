"""
HURIDOCS PDF Layout Analysis Integration
Uses professional layout analysis model for accurate PDF structure understanding
"""
import httpx
import structlog
from typing import Dict, List, Any, Optional
from pathlib import Path
import base64
import json

logger = structlog.get_logger()

class HURIDOCSLayoutAnalyzer:
    """Integrates with HURIDOCS PDF layout analysis service"""
    
    def __init__(self, service_url: str = "http://huridocs-layout:5060"):
        self.service_url = service_url
        self.client = httpx.Client(timeout=60.0)
    
    def analyze_pdf_layout(self, pdf_path: str, fast: bool = False) -> Optional[Dict[str, Any]]:
        """
        Analyze PDF layout using HURIDOCS service
        Returns structured layout information with spatial coordinates
        """
        try:
            # Check if service is available
            try:
                response = self.client.get(f"{self.service_url}/info", timeout=5.0)
                if response.status_code != 200:
                    logger.warning("huridocs_service_unavailable", status=response.status_code)
                    return None
            except Exception as e:
                logger.warning("huridocs_service_not_reachable", error=str(e))
                return None
            
            # Read PDF file
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                logger.error("pdf_file_not_found", path=pdf_path)
                return None
            
            # Prepare file for upload
            with open(pdf_file, "rb") as f:
                files = {"file": (pdf_file.name, f, "application/pdf")}
                data = {"fast": "true" if fast else "false"}
                
                # Call HURIDOCS API
                response = self.client.post(
                    self.service_url,
                    files=files,
                    data=data,
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    layout_data = response.json()
                    # HURIDOCS may return a list or dict - handle both
                    if isinstance(layout_data, list):
                        # If it's a list, wrap it in a dict with 'pages' key
                        layout_data = {"pages": layout_data}
                    elif not isinstance(layout_data, dict):
                        logger.warning("huridocs_unexpected_response_format", 
                                     response_type=type(layout_data).__name__)
                        return None
                    
                    logger.info("huridocs_layout_analysis_success", 
                              pages=len(layout_data.get("pages", [])))
                    return layout_data
                else:
                    logger.error("huridocs_analysis_failed", 
                               status=response.status_code,
                               error=response.text[:200])
                    return None
                    
        except Exception as e:
            logger.error("huridocs_analysis_error", error=str(e), exc_info=True)
            return None
    
    def extract_text_with_layout(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text from layout analysis results with proper structure
        Returns text organized by sections and columns
        HURIDOCS returns: pages = list of segments, each segment has: left, top, width, height, text, type
        """
        if not layout_data:
            return {"text": "", "sections": {}, "columns": {}, "layout_info": {}}
        
        # Handle different response formats
        pages = layout_data.get("pages", [])
        if not pages and isinstance(layout_data, list):
            pages = layout_data
        
        if not pages:
            return {"text": "", "sections": {}, "columns": {}, "layout_info": {}}
        
        all_text = []
        sections = {}
        columns = {}
        all_segments = []
        
        # HURIDOCS format: pages is a list of segments directly
        # Each segment has: left, top, width, height, page_number, text, type
        for segment in pages:
            if not isinstance(segment, dict):
                continue
                
            segment_type = segment.get("type", "").lower()
            text = segment.get("text", "").strip()
            left = segment.get("left", 0)
            top = segment.get("top", 0)
            width = segment.get("width", 0)
            height = segment.get("height", 0)
            page_number = segment.get("page_number", 0)
            page_width = segment.get("page_width", 0)
            page_height = segment.get("page_height", 0)
            
            # Create bbox dict for compatibility
            bbox = {"x": left, "y": top, "width": width, "height": height}
            
            if text:
                all_text.append(text)
                all_segments.append({
                    "text": text,
                    "type": segment_type,
                    "bbox": bbox,
                    "left": left,
                    "top": top,
                    "page": page_number,
                    "page_width": page_width,
                    "page_height": page_height
                })
                
                # Classify by type (title, text, etc.)
                if segment_type == "title":
                    # This might be a section header
                    if text.upper() in ["EXPERIENCE", "WORK EXPERIENCE", "EDUCATION", 
                                       "SKILLS", "PROJECTS", "CERTIFICATIONS"]:
                        section_name = text.upper()
                        if f"page_{page_number}" not in sections:
                            sections[f"page_{page_number}"] = {}
                        sections[f"page_{page_number}"][section_name] = {
                            "start_line": len(all_text) - 1,
                            "bbox": bbox
                        }
        
        # Detect columns based on spatial positions (left coordinate)
        if all_segments:
            # Get page width from segments (most segments should have it)
            page_widths = [s.get("page_width", 0) for s in all_segments 
                          if s.get("page_width", 0) > 0]
            avg_page_width = sum(page_widths) / len(page_widths) if page_widths else 0
            
            logger.info("huridocs_column_detection_start", 
                       segments_count=len(all_segments),
                       avg_page_width=avg_page_width)
            
            # Get all left positions
            left_positions = []
            for s in all_segments:
                if isinstance(s, dict):
                    left = s.get("left", 0)
                    if left > 0:
                        left_positions.append(left)
            
            if left_positions and avg_page_width > 0:
                sorted_left = sorted(set(left_positions))  # Unique positions
                min_left = min(left_positions)
                max_left = max(left_positions)
                
                # Strategy 1: Find clusters of left positions (two-column layout)
                # Group positions into clusters
                clusters = []
                current_cluster = [sorted_left[0]]
                
                for i in range(1, len(sorted_left)):
                    gap = sorted_left[i] - sorted_left[i-1]
                    if gap < 50:  # Small gap, same cluster
                        current_cluster.append(sorted_left[i])
                    else:  # Large gap, new cluster
                        if current_cluster:
                            clusters.append(current_cluster)
                        current_cluster = [sorted_left[i]]
                
                if current_cluster:
                    clusters.append(current_cluster)
                
                # Strategy 2: Use page width midpoint (fallback)
                midpoint = avg_page_width / 2
                
                # Determine separator
                separator_x = midpoint  # Default
                
                if len(clusters) >= 2:
                    # Two-column layout detected - use gap between clusters
                    left_cluster_max = max(clusters[0])
                    right_cluster_min = min(clusters[1])
                    separator_x = (left_cluster_max + right_cluster_min) / 2
                    logger.info("huridocs_column_separator_from_clusters", 
                              separator=separator_x, 
                              left_cluster_max=left_cluster_max,
                              right_cluster_min=right_cluster_min,
                              clusters=len(clusters))
                else:
                    # Try gap-based approach
                    gaps = []
                    for i in range(len(sorted_left) - 1):
                        gap = sorted_left[i+1] - sorted_left[i]
                        if gap > 80:  # Significant gap
                            gaps.append((sorted_left[i], sorted_left[i+1], gap))
                    
                    if gaps:
                        largest_gap = max(gaps, key=lambda x: x[2])
                        gap_size = largest_gap[2]
                        # Only use gap if it's substantial and reasonable (< 50% of page width)
                        if gap_size > 80 and gap_size < (avg_page_width * 0.5):
                            separator_x = (largest_gap[0] + largest_gap[1]) / 2
                            logger.info("huridocs_column_separator_from_gap", 
                                      separator=separator_x, gap_size=gap_size)
                        else:
                            logger.info("huridocs_column_separator_from_midpoint", 
                                      separator=separator_x, page_width=avg_page_width)
                    else:
                        logger.info("huridocs_column_separator_from_midpoint", 
                                  separator=separator_x, page_width=avg_page_width)
                
                # Split segments into columns (maintain order by top position)
                left_segments = []
                right_segments = []
                
                for s in all_segments:
                    left = s.get("left", 0)
                    top = s.get("top", 0)
                    
                    if left < separator_x:
                        left_segments.append((top, s))
                    else:
                        right_segments.append((top, s))
                
                # Sort by top position to maintain reading order
                left_segments.sort(key=lambda x: x[0])
                right_segments.sort(key=lambda x: x[0])
                
                # Extract text maintaining order
                left_text_lines = [seg[1].get("text", "").strip() 
                                  for seg in left_segments 
                                  if seg[1].get("text", "").strip()]
                right_text_lines = [seg[1].get("text", "").strip() 
                                   for seg in right_segments 
                                   if seg[1].get("text", "").strip()]
                
                left_text = "\n".join(left_text_lines)
                right_text = "\n".join(right_text_lines)
                
                # Check if we have a clear two-column layout
                # Both columns should have substantial content
                left_ratio = len(left_text) / len(left_text + right_text) if (left_text + right_text) else 0
                right_ratio = len(right_text) / len(left_text + right_text) if (left_text + right_text) else 0
                
                # Both columns should have at least 20% of content and minimum 100 chars
                if (left_text.strip() and right_text.strip() and 
                    len(left_text) > 100 and len(right_text) > 100 and
                    left_ratio > 0.15 and right_ratio > 0.15):
                    columns["page_0"] = {
                        "left": left_text,
                        "right": right_text,
                        "has_columns": True,
                        "separator_x": separator_x,
                        "left_count": len(left_segments),
                        "right_count": len(right_segments)
                    }
                    logger.info("huridocs_columns_detected", 
                              left_length=len(left_text), 
                              right_length=len(right_text),
                              left_segments=len(left_segments),
                              right_segments=len(right_segments),
                              separator=separator_x)
                else:
                    logger.info("huridocs_columns_not_detected", 
                              left_length=len(left_text),
                              right_length=len(right_text),
                              left_ratio=left_ratio,
                              right_ratio=right_ratio)
        
        full_text = "\n".join(all_text)
        
        return {
            "text": full_text,
            "sections": sections,
            "columns": columns,
            "layout_info": {
                "has_columns": len(columns) > 0,
                "total_pages": len(set(s.get("page", 0) for s in all_segments)) if all_segments else 0,
                "total_segments": len(all_segments)
            }
        }
    
    def get_experience_section(self, layout_data: Dict[str, Any]) -> Optional[str]:
        """Extract experience section text using layout analysis"""
        extracted = self.extract_text_with_layout(layout_data)
        
        # Try to find experience section in structured data
        for page_sections in extracted["sections"].values():
            if "EXPERIENCE" in page_sections or "WORK EXPERIENCE" in page_sections:
                # Get section boundaries and extract text
                section_info = page_sections.get("EXPERIENCE") or page_sections.get("WORK EXPERIENCE")
                start_line = section_info.get("start_line", 0)
                
                # Extract from that point onwards until next section
                lines = extracted["text"].split("\n")
                exp_lines = []
                in_section = False
                
                for i, line in enumerate(lines):
                    line_upper = line.upper().strip()
                    if i >= start_line:
                        # Check if we hit next major section
                        if any(keyword in line_upper for keyword in 
                              ["EDUCATION", "PROJECTS", "SKILLS", "CERTIFICATIONS"]):
                            if in_section:
                                break
                        in_section = True
                        exp_lines.append(line)
                
                return "\n".join(exp_lines)
        
        # Fallback: use full text
        return extracted["text"]
    
    def get_segmented_experience_data(self, layout_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract experience data using HURIDOCS segmentation types
        Uses 'Title' type segments for job titles and 'Text' segments for companies/descriptions
        """
        if not layout_data:
            return {"titles": [], "segments": [], "text": ""}
        
        pages = layout_data.get("pages", [])
        if not pages and isinstance(layout_data, list):
            pages = layout_data
        
        if not pages:
            return {"titles": [], "segments": [], "text": ""}
        
        # Find experience section start
        experience_started = False
        experience_segments = []
        title_segments = []
        
        for segment in pages:
            if not isinstance(segment, dict):
                continue
            
            segment_type = segment.get("type", "").lower()
            text = segment.get("text", "").strip()
            left = segment.get("left", 0)
            top = segment.get("top", 0)
            
            # Check if this is experience section header
            if segment_type in ["title", "section header"]:
                text_upper = text.upper()
                if "EXPERIENCE" in text_upper or "WORK" in text_upper:
                    experience_started = True
                    continue
            
            # If we're in experience section, collect segments
            if experience_started:
                # Check if we hit next major section
                if segment_type in ["title", "section header"]:
                    if any(keyword in text.upper() for keyword in 
                          ["EDUCATION", "PROJECTS", "SKILLS", "CERTIFICATIONS", "PROFILE"]):
                        break  # End of experience section
                
                # Collect title segments (likely job titles)
                if segment_type == "title":
                    title_segments.append({
                        "text": text,
                        "left": left,
                        "top": top,
                        "type": segment_type
                    })
                
                # Collect all segments in experience section
                experience_segments.append({
                    "text": text,
                    "type": segment_type,
                    "left": left,
                    "top": top,
                    "width": segment.get("width", 0),
                    "height": segment.get("height", 0),
                    "page_number": segment.get("page_number", 0)
                })
        
        # Sort segments by top position (reading order)
        experience_segments.sort(key=lambda x: (x.get("page_number", 0), x.get("top", 0)))
        title_segments.sort(key=lambda x: (x.get("top", 0)))
        
        # Extract text maintaining order
        exp_text = "\n".join([seg["text"] for seg in experience_segments if seg["text"]])
        
        return {
            "titles": [seg["text"] for seg in title_segments],
            "segments": experience_segments,
            "text": exp_text,
            "has_segmentation": True
        }
    
    def close(self):
        """Close HTTP client"""
        self.client.close()

# Global instance
huridocs_analyzer = HURIDOCSLayoutAnalyzer()

