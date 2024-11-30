from mangum import Adapter
from src.main import app

# Create handler for Vercel
handler = Adapter(app) 