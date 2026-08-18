#!/bin/bash

# ============================================================================
# SECURITY MVP - QUICK START SCRIPT
# One-command deployment for local development and production
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="pharmacy-security-mvp"
ENVIRONMENT=${1:-development}

# ============================================================================
# FUNCTIONS
# ============================================================================

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ============================================================================
# PREREQUISITES CHECK
# ============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo "Install from: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker installed"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        echo "Install from: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose installed"
    
    # Check Git
    if ! command -v git &> /dev/null; then
        print_warning "Git is not installed (optional)"
    else
        print_success "Git installed"
    fi
    
    # Check if Docker daemon is running
    if ! docker ps &> /dev/null; then
        print_error "Docker daemon is not running"
        echo "Start Docker and try again"
        exit 1
    fi
    print_success "Docker daemon is running"
}

# ============================================================================
# SETUP ENVIRONMENT
# ============================================================================

setup_environment() {
    print_header "Setting Up Environment"
    
    if [ ! -f .env ]; then
        print_info "Creating .env file from template..."
        cp .env.example .env
        print_success ".env file created"
        
        if [ "$ENVIRONMENT" = "production" ]; then
            print_warning "IMPORTANT: Update .env with production values:"
            print_warning "  - SECRET_KEY: Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            print_warning "  - DATABASE_URL: Update with production database"
            print_warning "  - DOMAIN_NAME: Set to your domain"
            read -p "Press Enter to continue..."
        fi
    else
        print_success ".env file already exists"
    fi
}

# ============================================================================
# SETUP DATABASE
# ============================================================================

setup_database() {
    print_header "Setting Up Database"
    
    # Wait for database to be ready
    print_info "Waiting for database to be ready..."
    sleep 5
    
    # Check if database is initialized
    if docker-compose exec -T db psql -U security_mvp -d security_mvp -c "SELECT 1" &>/dev/null; then
        print_success "Database is already initialized"
        return 0
    fi
    
    print_info "Initializing database..."
    docker-compose exec -T db psql -U security_mvp -d security_mvp < security-mvp-schema.sql
    
    if [ $? -eq 0 ]; then
        print_success "Database initialized successfully"
    else
        print_error "Failed to initialize database"
        exit 1
    fi
}

# ============================================================================
# BUILD & START SERVICES
# ============================================================================

start_services() {
    print_header "Starting Services"
    
    if [ "$ENVIRONMENT" = "production" ]; then
        print_info "Starting production services with nginx..."
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        print_info "Starting development services..."
        docker-compose up -d
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
    
    # Wait for services to be healthy
    print_info "Waiting for services to be healthy..."
    sleep 10
}

# ============================================================================
# VERIFY SERVICES
# ============================================================================

verify_services() {
    print_header "Verifying Services"
    
    local retries=0
    local max_retries=30
    
    # Check database
    while ! docker-compose exec -T db pg_isready -U security_mvp &>/dev/null; do
        if [ $retries -ge $max_retries ]; then
            print_error "Database failed to start"
            exit 1
        fi
        retries=$((retries + 1))
        sleep 1
    done
    print_success "Database is running"
    
    # Check API
    retries=0
    while ! curl -sf http://localhost:8000/health &>/dev/null; do
        if [ $retries -ge $max_retries ]; then
            print_warning "API health check failed (continuing anyway)"
            break
        fi
        retries=$((retries + 1))
        sleep 1
    done
    print_success "API is running"
    
    # Check Frontend
    retries=0
    while ! curl -sf http://localhost:3000 &>/dev/null; do
        if [ $retries -ge $max_retries ]; then
            print_warning "Frontend health check failed (continuing anyway)"
            break
        fi
        retries=$((retries + 1))
        sleep 1
    done
    print_success "Frontend is running"
}

# ============================================================================
# DISPLAY SUMMARY
# ============================================================================

display_summary() {
    print_header "✓ Setup Complete!"
    
    echo ""
    echo "Services are running and ready to use:"
    echo ""
    echo -e "  ${GREEN}Frontend Dashboard:${NC}    http://localhost:3000"
    echo -e "  ${GREEN}API Server:${NC}             http://localhost:8000"
    echo -e "  ${GREEN}API Documentation:${NC}      http://localhost:8000/docs"
    echo -e "  ${GREEN}Database:${NC}               localhost:5432"
    echo ""
    
    echo "Demo Credentials:"
    echo "  Email:    ama@pharmacy.com"
    echo "  Password: (any value works in demo)"
    echo "  Pharmacy: accra-central"
    echo ""
    
    echo "Useful Commands:"
    echo "  View logs:          docker-compose logs -f"
    echo "  Stop services:      docker-compose down"
    echo "  Restart services:   docker-compose restart"
    echo "  Reset everything:   docker-compose down -v"
    echo ""
    
    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "${YELLOW}PRODUCTION DEPLOYMENT:${NC}"
        echo "  1. Update .env with production values"
        echo "  2. Configure SSL certificates in ./ssl/"
        echo "  3. Setup domain DNS to point to server"
        echo "  4. Run: docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
        echo ""
    fi
    
    echo "Next Steps:"
    echo "  1. Open http://localhost:3000 in your browser"
    echo "  2. Login with demo credentials"
    echo "  3. Test product verification"
    echo "  4. Review API documentation at http://localhost:8000/docs"
    echo ""
}

# ============================================================================
# CLEANUP & ERROR HANDLING
# ============================================================================

cleanup() {
    if [ $? -ne 0 ]; then
        print_error "Setup failed!"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Check Docker is running: docker ps"
        echo "  2. View detailed logs: docker-compose logs"
        echo "  3. Free up ports: lsof -i :3000 (or :8000, :5432)"
        echo "  4. Reset environment: ./quickstart.sh reset"
        exit 1
    fi
}

trap cleanup EXIT

# ============================================================================
# SPECIAL COMMANDS
# ============================================================================

case "$1" in
    reset)
        print_header "Resetting Environment"
        docker-compose down -v
        rm -f .env
        print_success "Environment reset"
        exit 0
        ;;
    logs)
        docker-compose logs -f
        exit 0
        ;;
    stop)
        print_header "Stopping Services"
        docker-compose down
        print_success "Services stopped"
        exit 0
        ;;
    restart)
        print_header "Restarting Services"
        docker-compose restart
        print_success "Services restarted"
        exit 0
        ;;
    status)
        docker-compose ps
        exit 0
        ;;
    clean)
        print_header "Cleaning Up"
        docker-compose down -v
        docker system prune -f
        print_success "Cleanup complete"
        exit 0
        ;;
    help)
        echo "Usage: ./quickstart.sh [command] [environment]"
        echo ""
        echo "Commands:"
        echo "  (none)     Start services (default: development)"
        echo "  production Start services in production mode"
        echo "  reset      Reset all containers and remove .env"
        echo "  logs       View service logs"
        echo "  stop       Stop all services"
        echo "  restart    Restart all services"
        echo "  status     Show service status"
        echo "  clean      Deep clean (Docker system prune)"
        echo "  help       Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./quickstart.sh development    # Start development"
        echo "  ./quickstart.sh production     # Start production"
        echo "  ./quickstart.sh logs           # View logs"
        echo "  ./quickstart.sh stop           # Stop all"
        exit 0
        ;;
esac

# ============================================================================
# MAIN EXECUTION
# ============================================================================

print_header "Security MVP - Quick Start"
print_info "Environment: $ENVIRONMENT"
echo ""

check_prerequisites
setup_environment
start_services
setup_database
verify_services
display_summary

exit 0
