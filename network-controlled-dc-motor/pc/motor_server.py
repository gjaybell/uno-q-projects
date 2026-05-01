from http.server import BaseHTTPRequestHandler, HTTPServer

command = "stop"

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        global command

        if self.path == "/forward":
            command = "forward"
        elif self.path == "/reverse":
            command = "reverse"
        elif self.path == "/stop":
            command = "stop"
        elif self.path == "/cmd":
            pass

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if self.path == "/cmd":
            self.wfile.write(command.encode())
        else:
            self.wfile.write(f"""
            <h1>Motor Control</h1>
            <a href="/forward">Forward</a><br>
            <a href="/reverse">Reverse</a><br>
            <a href="/stop">Stop</a>
            """.encode())

server = HTTPServer(("0.0.0.0", 5000), Handler)
print("Control server running on port 5000")
server.serve_forever()
