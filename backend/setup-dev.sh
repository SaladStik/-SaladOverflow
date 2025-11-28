#!/bin/bash

# SaladOverflow Development Environment Setup Script

echo "🥗 Setting up SaladOverflow development environment..."

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    echo "✅ Docker is running"
}

# Function to start services
start_services() {
    echo "🚀 Starting MariaDB and Redis..."
    docker-compose up -d mariadb redis
    
    echo "⏳ Waiting for services to be ready..."
    sleep 10
    
    # Check MariaDB health
    echo "🔍 Checking MariaDB connection..."
    docker-compose exec -T mariadb mysql -u salad_user -psalad_password -e "SELECT 'Connection successful!' as status;" saladoverflow
    
    # Check Redis health
    echo "🔍 Checking Redis connection..."
    docker-compose exec -T redis redis-cli ping
    
    echo "✅ Development environment is ready!"
    echo ""
    echo "📊 Services running:"
    echo "   - MariaDB: localhost:3306"
    echo "   - Redis: localhost:6379"
    echo ""
    echo "🌐 Optional web tools (run with --tools flag):"
    echo "   - phpMyAdmin: http://localhost:8080"
    echo "   - Redis Commander: http://localhost:8081"
    echo ""
    echo "🚀 Start your FastAPI server:"
    echo "   python run.py"
}

# Function to start with tools
start_with_tools() {
    echo "🚀 Starting all services including web tools..."
    docker-compose --profile tools up -d
    
    echo "⏳ Waiting for services to be ready..."
    sleep 15
    
    echo "✅ All services ready!"
    echo ""
    echo "📊 Services running:"
    echo "   - MariaDB: localhost:3306"
    echo "   - Redis: localhost:6379"
    echo "   - phpMyAdmin: http://localhost:8080"
    echo "   - Redis Commander: http://localhost:8081"
}

# Parse command line arguments
case "$1" in
    --tools)
        check_docker
        start_with_tools
        ;;
    --stop)
        echo "🛑 Stopping all services..."
        docker-compose down
        echo "✅ Services stopped"
        ;;
    --reset)
        echo "⚠️  Stopping services and removing data volumes..."
        read -p "This will delete all database data. Continue? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            docker-compose down -v
            echo "✅ Services stopped and data cleared"
        else
            echo "❌ Operation cancelled"
        fi
        ;;
    *)
        check_docker
        start_services
        ;;
esac
