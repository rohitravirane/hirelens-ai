#!/bin/bash
# Complete rebuild script for HireLens AI Vision-First System

set -e  # Exit on error

echo "=========================================="
echo "HireLens AI - Complete Rebuild"
echo "=========================================="
echo ""
echo "This will rebuild the entire system with:"
echo "  ✓ PyTesseract (OCR support)"
echo "  ✓ Updated transformers (Qwen2 support)"
echo "  ✓ All optimizations"
echo ""
echo "Press Ctrl+C to cancel, or wait 5 seconds..."
sleep 5

echo ""
echo "Step 1: Stopping all containers..."
docker-compose down

echo ""
echo "Step 2: Rebuilding backend container (this may take 5-10 minutes)..."
docker-compose build --no-cache backend

echo ""
echo "Step 3: Rebuilding celery-worker..."
docker-compose build --no-cache celery-worker

echo ""
echo "Step 4: Starting all services..."
docker-compose up -d

echo ""
echo "Step 5: Waiting for services to be ready..."
sleep 10

echo ""
echo "Step 6: Checking container status..."
docker-compose ps

echo ""
echo "=========================================="
echo "Rebuild Complete!"
echo "=========================================="
echo ""
echo "Check logs with:"
echo "  docker-compose logs -f celery-worker"
echo ""
echo "Test the system with:"
echo "  docker-compose exec backend python scripts/reprocess_all_resumes.py"
echo ""

