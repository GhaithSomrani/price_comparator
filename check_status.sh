#!/bin/bash

###############################################################################
# System Status Check Script
# Quickly check the status of all components
###############################################################################

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Price Comparator - System Status Check      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}\n"

# Check MongoDB
echo -e "${YELLOW}[1/5] MongoDB Status:${NC}"
if systemctl is-active --quiet mongodb; then
    echo -e "  ${GREEN}✓ Running${NC}"
    if command -v mongosh &> /dev/null; then
        MONGO_STATUS=$(mongosh --eval "db.adminCommand('ping').ok" --quiet 2>/dev/null)
        if [ "$MONGO_STATUS" = "1" ]; then
            echo -e "  ${GREEN}✓ Accessible${NC}"
        else
            echo -e "  ${RED}✗ Not accessible${NC}"
        fi
    fi
else
    echo -e "  ${RED}✗ Not running${NC}"
fi

# Check Flask API
echo -e "\n${YELLOW}[2/5] Flask API Status:${NC}"
if systemctl is-active --quiet price-comparator-api.service; then
    echo -e "  ${GREEN}✓ Service running${NC}"

    # Check if API responds
    if curl -s -f http://localhost:5000/products > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ API responding on port 5000${NC}"
    else
        echo -e "  ${RED}✗ API not responding${NC}"
    fi
else
    echo -e "  ${RED}✗ Service not running${NC}"
    echo -e "  ${YELLOW}  Start with: sudo systemctl start price-comparator-api.service${NC}"
fi

# Check Database
echo -e "\n${YELLOW}[3/5] Database Status:${NC}"
if command -v mongosh &> /dev/null; then
    PRODUCT_COUNT=$(mongosh product_comparator --quiet --eval "db.products.countDocuments()" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✓ Database: product_comparator${NC}"
        echo -e "  ${GREEN}✓ Products: $PRODUCT_COUNT${NC}"

        # Get latest product date
        LATEST=$(mongosh product_comparator --quiet --eval "db.products.find().sort({DateAjout: -1}).limit(1).toArray()[0]?.DateAjout" 2>/dev/null)
        if [ ! -z "$LATEST" ]; then
            echo -e "  ${GREEN}✓ Latest product: $LATEST${NC}"
        fi
    else
        echo -e "  ${RED}✗ Cannot access database${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ mongosh not installed${NC}"
fi

# Check Scrapy Environment
echo -e "\n${YELLOW}[4/5] Scrapy Environment:${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/price_comparator/venv" ]; then
    echo -e "  ${GREEN}✓ Virtual environment exists${NC}"

    # Check if scrapy is installed
    if [ -f "$SCRIPT_DIR/price_comparator/venv/bin/scrapy" ]; then
        echo -e "  ${GREEN}✓ Scrapy installed${NC}"
    else
        echo -e "  ${RED}✗ Scrapy not found${NC}"
    fi
else
    echo -e "  ${RED}✗ Virtual environment not found${NC}"
fi

# Check Cron Jobs
echo -e "\n${YELLOW}[5/5] Scheduled Tasks:${NC}"
CRON_COUNT=$(crontab -l 2>/dev/null | grep -c "run_tunisianet_scraper.sh")
if [ $CRON_COUNT -gt 0 ]; then
    echo -e "  ${GREEN}✓ Scraper scheduled (every 12 hours)${NC}"
    crontab -l | grep "run_tunisianet_scraper.sh" | sed 's/^/  /'
else
    echo -e "  ${YELLOW}⚠ No scheduled scraper tasks found${NC}"
fi

# Check recent scraper runs
if [ -f "$SCRIPT_DIR/scraper.log" ]; then
    LAST_RUN=$(grep -a "Starting TunisiaNet scraper" "$SCRIPT_DIR/scraper.log" | tail -1)
    if [ ! -z "$LAST_RUN" ]; then
        echo -e "  ${GREEN}✓ Last scraper run: $LAST_RUN${NC}"
    fi
fi

# Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Quick Actions                     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo -e "  View API logs:      ${YELLOW}sudo journalctl -u price-comparator-api.service -f${NC}"
echo -e "  View scraper logs:  ${YELLOW}tail -f $SCRIPT_DIR/scraper.log${NC}"
echo -e "  Run scraper now:    ${YELLOW}$SCRIPT_DIR/run_tunisianet_scraper.sh${NC}"
echo -e "  Manage services:    ${YELLOW}$SCRIPT_DIR/manage_services.sh${NC}"
echo -e "  Test API:           ${YELLOW}curl http://localhost:5000/products${NC}"

echo ""
