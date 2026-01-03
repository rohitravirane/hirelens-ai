#!/usr/bin/env python3
"""
Debug script to check why LayoutLMv3 is not being used
Run: docker-compose exec backend python scripts/debug_layoutlm_usage.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import structlog
from app.resumes.layout_parser.layout_parser import LayoutParser
from app.resumes.layout_parser.layoutlm_processor import LayoutLMProcessor

logger = structlog.get_logger()

def check_layoutlm_initialization():
    """Check if LayoutLMv3 is properly initialized"""
    print("\n" + "="*80)
    print("LAYOUTLMV3 INITIALIZATION CHECK")
    print("="*80 + "\n")
    
    try:
        print("1. Checking LayoutLMProcessor initialization...")
        processor = LayoutLMProcessor()
        print(f"   ✅ LayoutLMProcessor created")
        print(f"   - Available: {processor.is_available}")
        print(f"   - Processor exists: {processor.processor is not None}")
        print(f"   - Model exists: {processor.model is not None}")
        print(f"   - Device: {processor.device}")
        
        if not processor.is_available:
            print("\n   ❌ LayoutLMv3 is NOT available!")
            print("   This means vision-first parsing will use text-based fallback.")
            return False
        
        print("\n   ✅ LayoutLMv3 is available and ready!")
        return True
        
    except Exception as e:
        print(f"\n   ❌ Error initializing LayoutLMProcessor: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_layout_parser():
    """Check if LayoutParser can be initialized"""
    print("\n" + "="*80)
    print("LAYOUT PARSER INITIALIZATION CHECK")
    print("="*80 + "\n")
    
    try:
        print("1. Checking LayoutParser initialization...")
        layout_parser = LayoutParser()
        print(f"   ✅ LayoutParser created")
        print(f"   - LayoutLM available: {layout_parser.layoutlm_processor.is_available}")
        print(f"   - Semantic normalizer available: {layout_parser.semantic_normalizer is not None and layout_parser.semantic_normalizer.is_available if layout_parser.semantic_normalizer else False}")
        print(f"   - Device: {layout_parser.device}")
        
        return True
        
    except Exception as e:
        print(f"\n   ❌ Error initializing LayoutParser: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ai_parser_import():
    """Check if ai_parser can import LayoutParser"""
    print("\n" + "="*80)
    print("AI PARSER IMPORT CHECK")
    print("="*80 + "\n")
    
    try:
        print("1. Checking if ai_parser can import LayoutParser...")
        from app.resumes.layout_parser import LayoutParser
        print("   ✅ LayoutParser can be imported")
        
        print("\n2. Testing LayoutParser instantiation...")
        layout_parser = LayoutParser()
        print("   ✅ LayoutParser can be instantiated")
        
        return True
        
    except Exception as e:
        print(f"\n   ❌ Error importing/instantiating LayoutParser: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("LAYOUTLMV3 USAGE DEBUG")
    print("="*80)
    
    # Check 1: LayoutLMProcessor initialization
    layoutlm_ok = check_layoutlm_initialization()
    
    # Check 2: LayoutParser initialization
    layout_parser_ok = check_layout_parser()
    
    # Check 3: AI Parser import
    ai_parser_ok = check_ai_parser_import()
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"LayoutLMProcessor: {'✅ OK' if layoutlm_ok else '❌ FAILED'}")
    print(f"LayoutParser: {'✅ OK' if layout_parser_ok else '❌ FAILED'}")
    print(f"AI Parser Import: {'✅ OK' if ai_parser_ok else '❌ FAILED'}")
    
    if layoutlm_ok and layout_parser_ok and ai_parser_ok:
        print("\n✅ All checks passed! LayoutLMv3 should be working.")
        print("   If it's still not being used, check:")
        print("   1. Celery worker logs for processing errors")
        print("   2. PDF file path is valid and accessible")
        print("   3. No exceptions during _parse_with_layout call")
    else:
        print("\n❌ Some checks failed. Fix the issues above before proceeding.")
    print("="*80 + "\n")

