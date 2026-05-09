# Docker Setup - Quick Start (Fully Containerized)

## Your Setup
- **SQL Server**: Docker Container (Port 1433)
- **Redis**: Docker Container (Port 6379)
- **Backend**: Docker Container (Port 8000)
- **Frontend**: Docker Container (Port 5500/80)
- **Network**: All services on `pdms_network` bridge

## Prerequisites
1. Docker Desktop installed and running
2. WSL2 backend enabled (for Windows)
3. At least 4GB available memory

## Quick Start

### 1. Build Docker Images
```bash
cd /Patient_Data_Management_System_2026
docker-compose build
```

### 2. Start All Containers
```bash
docker-compose up -d
```

### 3. Verify Services Running
```bash
# Check container status
docker-compose ps

# View backend logs (wait 30-60 seconds for SQL Server to initialize)
docker-compose logs -f backend

# View all logs
docker-compose logs -f
```

### 4. Create Database (First Time Only)
Open **SQL Server Management Studio (SSMS)**:
- Server: `localhost,1433`
- Authentication: SQL Server Authentication
- Login: `sa`
- Password: `password!123`

Then run:
```sql
CREATE DATABASE pdms_db;
```

Then run initialization scripts from `/database` folder in order:
- `00_create_database.sql` (optional, DB already created)
- `01_rbac.sql`
- `02_...` through `13_test_data.sql`

### 5. Access Services
- **Frontend**: http://localhost:5500
- **API Docs**: http://localhost:8000/docs
- **SQL Server**: `localhost,1433` (SSMS)
- **Redis**: `localhost:6379` (redis-cli)

## Service Details

### SQL Server Container
- Image: `mcr.microsoft.com/mssql/server:2022-latest` (Linux)
- SA Password: `password!123`
- Database: `pdms_db` (must be created manually)
- Volume: `mssql_data` (persistent)
- Memory: 2GB limit

### Redis Container
- Image: `redis:7-alpine`
- Persistence: Enabled (appendonly mode)
- Volume: `redis_data` (persistent)

### Backend Container
- Port: 8000
- Database URL: `mssql+pyodbc://sa:password!123@mssql:1433/pdms_db?driver=ODBC+Driver+17+for+SQL+Server`
- Redis URL: `redis://redis:6379/0`
- Volume: `./backend` (hot-reload in development)

### Frontend Container
- Port: 5500 (mapped from 80)
- Static files only (no reverse proxy)
- API calls direct to `http://localhost:8000`

## Troubleshooting

### Backend Cannot Connect to SQL Server
```bash
# Check logs
docker-compose logs backend

# Verify SQL Server is running
docker-compose logs mssql


```

### Backend Cannot Connect to Redis
```bash
# Check Redis logs
docker-compose logs redis

# Verify Redis is running
docker exec pdms-redis redis-cli ping
```

### Frontend Cannot Reach Backend (CORS Error)
- Frontend calls `http://localhost:8000` directly
- Backend has CORS enabled (allows all origins)
- Check browser console for full error

### Port Already in Use
```bash
# Find what's using port
netstat -ano | findstr :8000
netstat -ano | findstr :5500
netstat -ano | findstr :1433


### SQL Server Initialization Takes Time
- First startup may take 30-60 seconds
- Wait until "INFO: SQL Server is now ready for client connections" appears
- Then create database and run initialization scripts

## Common Commands

```bash
# Stop services (keeps data)
docker-compose stop

# Start stopped services
docker-compose start

# Restart all services
docker-compose restart

# Remove containers (keeps volumes/data)
docker-compose down

# Remove containers AND volumes (clean slate)
docker-compose down -v


# Shell into container
docker-compose exec backend bash
docker-compose exec frontend sh

# Execute command in container
docker exec pdms-backend uvicorn app.main:app --reload

# Rebuild specific service
docker-compose build --no-cache backend
```

## Environment Variables
Hardcoded in `docker-compose.yml`:
- `SECRET_KEY` - JWT secret (min 32 chars)
- `ALGORITHM` - HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES` - 30
- `REFRESH_TOKEN_EXPIRE_DAYS` - 7
- `DEBUG` - True
- `GEMINI_API_KEY` - Your API key

## File Structure
```
Patient_Data_Management_System_2026/
├── backend/
│   ├── Dockerfile.backend (with ODBC 17 driver)
│   ├── requirements.txt
│   └── app/
├── frontend/
│   ├── Dockerfile.frontend
│   ├── index.html
│   ├── js/
│   │   ├── config.js (BASE = "http://localhost:8000")
│   │   └── api.js
│   └── css/
├── database/
│   ├── 00_create_database.sql
│   ├── 01_rbac.sql
│   └── ...
├── nginx.conf (minimal - static only)
├── docker-compose.yml (4 services)
└── DOCKER_QUICK_START.md
```

## First-Time Setup Steps

1. **Build images**
   ```bash
   docker-compose build
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Wait for SQL Server** (30-60 seconds)
   ```bash
   docker-compose logs mssql
   # Look for "SQL Server is now ready for client connections"
   ```

4. **Create database in SSMS**
   - Connect: `localhost,1433` / `sa` / `password!123`
   - Execute: `CREATE DATABASE pdms_db;`

5. **Run initialization scripts**
   - Open all `.sql` files from `/database` in SSMS
   - Run in order: `00_...` through `13_test_data.sql`

6. **Access frontend**
   - Open http://localhost:5500
   - Login with test credentials from `13_test_data.sql`

7. **Test API**
   - http://localhost:8000/docs (Swagger)
   - http://localhost:8000/health (health check)

## Stopping & Cleanup

```bash
# Stop running (keeps data)
docker-compose stop

# Remove all (keeps volumes)
docker-compose down

# Full clean (removes volumes too)
docker-compose down -v

# Restart fresh
docker-compose down -v && docker-compose up -d
```

## Next Steps
1. `docker-compose build`
2. `docker-compose up -d`
3. Wait 60 seconds
4. Create database in SSMS
5. Run SQL scripts
6. Visit http://localhost:5500
