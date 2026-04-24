#!/bin/bash

# Configuration
SERVICE_NAME="tactical-bot"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
WORKING_DIR=$(pwd)
PYTHON_PATH="${WORKING_DIR}/venv/bin/python3"
USER=$(whoami)

install() {
    echo "Installing Tactical Bot Service..."
    
    # Create the systemd service file
    sudo bash -c "cat > ${SERVICE_FILE}" <<EOF
[Unit]
Description=Tactical Bot Scheduler
After=network.target

[Service]
User=${USER}
WorkingDirectory=${WORKING_DIR}
ExecStart=${PYTHON_PATH} scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Reload and Start
    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    sudo systemctl start ${SERVICE_NAME}
    
    echo "Done! Bot is now running in the background."
    echo "Use './manage.sh status' to check."
}

uninstall() {
    echo "Uninstalling Tactical Bot Service..."
    sudo systemctl stop ${SERVICE_NAME}
    sudo systemctl disable ${SERVICE_NAME}
    sudo rm ${SERVICE_FILE}
    sudo systemctl daemon-reload
    echo "Service removed."
}

status() {
    sudo systemctl status ${SERVICE_NAME}
}

logs() {
    tail -f logs/sync.log
}

case "$1" in
    install)
        install
        ;;
    uninstall)
        uninstall
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    *)
        echo "Usage: $0 {install|uninstall|status|logs}"
        exit 1
esac
