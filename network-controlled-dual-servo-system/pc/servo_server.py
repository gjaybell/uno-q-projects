from http.server import BaseHTTPRequestHandler, HTTPServer

servo1 = "90"
servo2 = "90"

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        global servo1, servo2

        print("Request:", self.path)

        # Handle slider updates
        if self.path.startswith("/set?"):
            try:
                query = self.path.split("?")[1]
                parts = query.split("&")

                for p in parts:
                    if p.startswith("s1="):
                        servo1 = p.split("=")[1]
                    if p.startswith("s2="):
                        servo2 = p.split("=")[1]
            except:
                pass

        # UNO Q polling endpoint
        elif self.path == "/cmd":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"{servo1},{servo2}".encode())
            return

        # Web UI
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        page = f"""
        <html>
        <body>
            <h1>Dual Servo Control</h1>

            <h3>Servo 1 (Pan)</h3>
            <input type="range" min="0" max="180" value="{servo1}"
                oninput="update()">

            <p>Value: <span id="v1">{servo1}</span></p>

            <h3>Servo 2 (Tilt)</h3>
            <input type="range" min="0" max="180" value="{servo2}"
                oninput="update()">

            <p>Value: <span id="v2">{servo2}</span></p>

            <script>
            function update() {{
                let s1 = document.getElementsByTagName('input')[0].value;
                let s2 = document.getElementsByTagName('input')[1].value;

                document.getElementById("v1").innerText = s1;
                document.getElementById("v2").innerText = s2;

                fetch(`/set?s1=${{s1}}&s2=${{s2}}`);
            }}
            </script>
        </body>
        </html>
        """

        self.wfile.write(page.encode())


server = HTTPServer(("0.0.0.0", 5000), Handler)
print("Servo server running on port 5000")
server.serve_forever()

