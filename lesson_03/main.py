import json
import logging
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote_plus

from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path()

jinja = Environment(loader=FileSystemLoader("templates"))


class MyFrameWork(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urlparse(self.path)
        match route.path:
            case "/":
                self.send_html("index.html")
            case "/contact":
                self.send_html("contact.html")
            case "/blog":
                self.render_template("blog.jinja")
            case _:
                file = BASE_DIR / route.path[1:]
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html("404.html", 404)

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-type", mime_type)
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(filename, "rb") as file:
            self.wfile.write(file.read())

    def render_template(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        with open("storage/db.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        template = jinja.get_template(filename)
        message = "Hello Vadym!"
        html = template.render(blogs=data, message=message)
        self.wfile.write(html.encode())

    def do_POST(self):
        size_data = self.headers.get("Content-Length")
        data = self.rfile.read(int(size_data))
        save_data(data)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()


def save_data(data):
    print(data)
    parse_data = unquote_plus(data.decode())
    print(parse_data)
    try:
        parse_dict = {
            key: value for key, value in [el.split("=") for el in parse_data.split("&")]
        }
        with open("data/data.json", "w", encoding="utf-8") as file:
            json.dump(parse_dict, file, ensure_ascii=False, indent=4)
    except ValueError as err:
        logging.error(err)
    except OSError as err:
        logging.error(err)


def run_server():
    server_address = ("localhost", 3000)
    httpd = HTTPServer(server_address, MyFrameWork)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s"
    )
    run_server()
