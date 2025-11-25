#!/bin/bash
# ============================================
# UNS Kobetsu Keiyakusho - Unix Startup Script
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}=========================================="
echo "  UNS Kobetsu Keiyakusho System"
echo "  Individual Contract Management"
echo -e "==========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}[ERROR] Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[INFO] Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}[WARNING] Please edit .env file with your settings.${NC}"
    echo ""
fi

# Parse command
ACTION="${1:-up}"

case "$ACTION" in
    up)
        echo -e "${GREEN}[INFO] Starting all services...${NC}"
        docker-compose up -d
        echo ""
        echo -e "${GREEN}[SUCCESS] Services started!${NC}"
        echo ""
        echo "Access points:"
        echo "  - Frontend:  http://localhost:3010"
        echo "  - Backend:   http://localhost:8010"
        echo "  - API Docs:  http://localhost:8010/docs"
        echo "  - Adminer:   http://localhost:8090"
        echo ""
        ;;
    down)
        echo -e "${YELLOW}[INFO] Stopping all services...${NC}"
        docker-compose down
        echo -e "${GREEN}[SUCCESS] Services stopped.${NC}"
        ;;
    restart)
        echo -e "${YELLOW}[INFO] Restarting all services...${NC}"
        docker-compose down
        docker-compose up -d
        echo -e "${GREEN}[SUCCESS] Services restarted.${NC}"
        ;;
    logs)
        echo -e "${BLUE}[INFO] Showing logs (Ctrl+C to exit)...${NC}"
        docker-compose logs -f
        ;;
    build)
        echo -e "${YELLOW}[INFO] Rebuilding all containers...${NC}"
        docker-compose build --no-cache
        docker-compose up -d
        echo -e "${GREEN}[SUCCESS] Containers rebuilt and started.${NC}"
        ;;
    clean)
        echo -e "${RED}[WARNING] This will remove all containers, volumes, and images.${NC}"
        read -p "Are you sure? (y/N): " confirm
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            docker-compose down -v --rmi local
            echo -e "${GREEN}[SUCCESS] Cleanup complete.${NC}"
        fi
        ;;
    migrate)
        echo -e "${BLUE}[INFO] Running database migrations...${NC}"
        docker-compose exec kobetsu-backend alembic upgrade head
        echo -e "${GREEN}[SUCCESS] Migrations complete.${NC}"
        ;;
    seed)
        echo -e "${BLUE}[INFO] Seeding database with sample data...${NC}"
        docker-compose exec kobetsu-backend python -m app.scripts.seed_data
        echo -e "${GREEN}[SUCCESS] Database seeded.${NC}"
        ;;
    status)
        echo -e "${BLUE}[INFO] Service status:${NC}"
        echo ""
        docker-compose ps
        ;;
    shell)
        echo -e "${BLUE}[INFO] Opening shell in backend container...${NC}"
        docker-compose exec kobetsu-backend /bin/bash
        ;;
    *)
        echo "Usage: ./start.sh [up|down|restart|logs|build|clean|migrate|seed|status|shell]"
        echo ""
        echo "Commands:"
        echo "  up       - Start all services (default)"
        echo "  down     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show service logs"
        echo "  build    - Rebuild containers from scratch"
        echo "  clean    - Remove all containers and volumes"
        echo "  migrate  - Run database migrations"
        echo "  seed     - Seed database with sample data"
        echo "  status   - Show service status"
        echo "  shell    - Open shell in backend container"
        ;;
esac
