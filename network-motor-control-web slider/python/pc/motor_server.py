from http.server import BaseHTTPRequestHandler, HTTPServer

command = "0"

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        global command

        print("Request:", self.path)

        if self.path.startswith("/set?speed="):
            try:
                command = self.path.split("=")[1]
            except:
                command = "0"

        elif self.path == "/cmd":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(command.encode())
            return

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        page = f"""
        <html>
        <body>
            <h1>Motor Control (Slider)</h1>

            <input type="range" min="-255" max="255" value="0"
                oninput="sendValue(this.value)">

            <p>Speed: <span id="val">0</span></p>

            <script>
            let timer;

            function sendValue(val) {{
                document.getElementById("val").innerText = val;

                clearTimeout(timer);
                timer = setTimeout(() => {{
                    fetch("/set?speed=" + val);
                }}, 100);
            }}
            </script>
        </body>
        </html>
        """

        self.wfile.write(page.encode())

server = HTTPServer(("0.0.0.0", 5000), Handler)
print("Slider control server running on port 5000")
server.serve_forever()
