#!/bin/sh
set -e

# Load environment variables from .env safely
if [ -f ".env" ]; then
    echo "Loading environment variables from .env..."
    export $(grep -v '^#' .env | sed 's/\r//g' | xargs)
fi

# Create superuser if VERSION matches
case "$(echo "$VERSION" | tr '[:upper:]' '[:lower:]')" in
    test)
        echo "Creating superuser..."
        python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username="$ADMIN_USER").exists():
    User.objects.create_superuser(
        username="$ADMIN_USER",
        password="$ADMIN_PASSWORD",
        email="$ADMIN_EMAIL"
    )
    print("Superuser created.")
else:
    print("Superuser already exists.")
EOF
        ;;
    *)
        echo "Skipping superuser creation (VERSION=$VERSION)"
        ;;
esac
