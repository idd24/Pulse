For a physical iOS device on the same Wi-Fi, you need --host 0.0.0.0. The default binds to 127.0.0.1  
(localhost only), so your phone can't reach it — it has to hit your Mac's LAN IP, and that requires
binding to all interfaces.

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
