@echo off
REM SaladOverflow Development Environment Setup Script for Windows

echo 🥗 Setting up SaladOverflow development environment...

REM Function to check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    exit /b 1
)
echo ✅ Docker is running

REM Parse command line arguments
if "%1"=="--tools" goto start_with_tools
if "%1"=="--stop" goto stop_services
if "%1"=="--reset" goto reset_services
goto start_services

:start_services
echo 🚀 Starting MariaDB and Redis...
docker-compose up -d mariadb redis

echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo 🔍 Checking MariaDB connection...
docker-compose exec -T mariadb mysql -u salad_user -psalad_password -e "SELECT 'Connection successful!' as status;" saladoverflow

echo 🔍 Checking Redis connection...
docker-compose exec -T redis redis-cli ping

echo ✅ Development environment is ready!
echo.
echo 📊 Services running:
echo    - MariaDB: localhost:3306
echo    - Redis: localhost:6379
echo.
echo 🌐 Optional web tools (run with --tools flag):
echo    - phpMyAdmin: http://localhost:8080
echo    - Redis Commander: http://localhost:8081
echo.
echo 🚀 Start your FastAPI server:
echo    python run.py
goto end

:start_with_tools
echo 🚀 Starting all services including web tools...
docker-compose --profile tools up -d

echo ⏳ Waiting for services to be ready...
timeout /t 15 /nobreak >nul

echo ✅ All services ready!
echo.
echo 📊 Services running:
echo    - MariaDB: localhost:3306
echo    - Redis: localhost:6379
echo    - phpMyAdmin: http://localhost:8080
echo    - Redis Commander: http://localhost:8081
goto end

:stop_services
echo 🛑 Stopping all services...
docker-compose down
echo ✅ Services stopped
goto end

:reset_services
echo ⚠️  Stopping services and removing data volumes...
set /p confirm="This will delete all database data. Continue? (y/N): "
if /i "%confirm%"=="y" (
    docker-compose down -v
    echo ✅ Services stopped and data cleared
) else (
    echo ❌ Operation cancelled
)
goto end

:end
pause
