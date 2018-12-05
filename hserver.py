import sys, os, traceback, logging, codecs, json
from StringIO import StringIO
from urlparse import parse_qs
import logging.config

from app.anf_data import AnfisaData

#========================================
class HServResponse:
    #========================================
    sContentTypes = {
        "html":   "text/html",
        "xml":    "text/xml",
        "css":    "text/css",
        "js":     "application/javascript",
        "png":    "image/png",
        "json":   "application/json",
        "xlsx":   (
            "application/application/"
            "vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }

    sErrorCodes = {
        202: "202 Accepted",
        204: "204 No Content",
        303: "303 See Other",
        400: "400 Bad Request",
        408: "408 Request Timeout",
        404: "404 Not Found",
        422: "422 Unprocessable Entity",
        423: "423 Locked",
        500: "500 Internal Error"}

    def __init__(self, start_response):
        self.mStartResponse = start_response

    def makeResponse(self, mode = "html", content = None, error = None,
            add_headers = None, without_decoding = False):
        response_status = "200 OK"
        if error is not None:
            response_status = self.sErrorCodes[error]
        if content is not None:
            if without_decoding:
                response_body = bytes(content)
            else:
                response_body = content.encode("utf-8")
            response_headers = [("Content-Type", self.sContentTypes[mode]),
                                ("Content-Length", str(len(response_body)))]
        else:
            response_body = response_status
            response_headers = []
        if add_headers is not None:
            response_headers += add_headers
        self.mStartResponse(response_status, response_headers)
        return [response_body]

#========================================
class HServHandler:
    sInstance = None
    sService  = None

    @classmethod
    def init(cls, config, in_container):
        cls.sInstance = cls(config, in_container)
        cls.sService  = AnfisaData.setup(config, in_container)

    @classmethod
    def request(cls, environ, start_response):
        return cls.sInstance.processRq(environ, start_response)

    def __init__(self, config, in_container):
        self.mFiles = config["files"]
        self.mHtmlBase = (config["html-base"]
            if in_container else None)
        if self.mHtmlBase and self.mHtmlBase.endswith('/'):
            self.mHtmlBase = self.mHtmlBase[:-1]

    def checkFileDir(self, path):
        for dirname, extensions in self.mFiles.items():
            for ext in extensions:
                if path.endswith(ext):
                    return dirname
        return None

    #===============================================
    def parseRequest(self, environ):
        path = environ["PATH_INFO"]
        if self.mHtmlBase and path.startswith(self.mHtmlBase):
            path = path[len(self.mHtmlBase):]
        if not path:
            path = "/"
        query_string = environ["QUERY_STRING"]

        query_args = dict()
        if query_string:
            for a, v in parse_qs(query_string).items():
                query_args[a] = v[0]

        if environ["REQUEST_METHOD"] == "POST":
            try:
                rq_body_size = int(environ.get('CONTENT_LENGTH', 0))
                rq_body = environ['wsgi.input'].read(rq_body_size)
                for a, v in parse_qs(rq_body).items():
                    query_args[a] = v[0].decode("utf-8")
            except Exception:
                rep = StringIO()
                traceback.print_exc(file = rep)
                log_record = rep.getvalue()
                logging.error(
                    "Exception on read request body:\n " + log_record)

        return path, query_args

    #===============================================
    def fileResponse(self, resp_h, dirname, fname,
            query_args, without_decoding):
        fpath = dirname + fname
        if not os.path.exists(fpath):
            return False
        if without_decoding:
            inp = open(fpath, "rb")
            content = inp.read()
        else:
            with codecs.open(fpath, "r", encoding = "utf-8") as inp:
                content = inp.read()
        inp.close()

        file_ext  = fname.rpartition('.')[2]
        add_headers = None

        if file_ext == ".xslx":
            add_headers = [("content-disposition",
                "attachment; filename=%s" %
                query_args.get("disp", fname.rpartition('/')[2]))]

        return resp_h.makeResponse(mode = file_ext,
            content = content, add_headers = add_headers,
            without_decoding = without_decoding)

    #===============================================
    def processRq(self, environ, start_response):
        resp_h = HServResponse(start_response)
        try:
            path, query_args = self.parseRequest(environ)
            dirname = self.checkFileDir(path)
            if dirname is not None:
                ret = self.fileResponse(resp_h,
                    dirname, path, query_args, True)
                if ret is not False:
                    return ret
            return self.sService.request(resp_h, path, query_args)
        except Exception:
            rep = StringIO()
            traceback.print_exc(file = rep)
            log_record = rep.getvalue()
            logging.error(
                "Exception on GET request:\n " + log_record)
            return resp_h.makeResponse(error = 500)

#========================================
def loadJSonConfig(config_file):
    with codecs.open(config_file, "r", encoding = "utf-8") as inp:
        content = inp.read()
    pre_config = json.loads(content)
    file_path_def = pre_config.get("file-path-def")
    if file_path_def:
        for key, value in file_path_def.items():
            content = content.replace('${%s}' % key, value)
    return json.loads(content)

#========================================
def setupHServer(config_file, in_container):
    if not os.path.exists(config_file):
        logging.critical("No config file provided (%s)" % config_file)
        sys.exit(2)
    config = loadJSonConfig(config_file)
    logging_config = config.get("logging")
    if logging_config:
        logging.config.dictConfig(logging_config)
        logging.basicConfig(level = 0)
    HServHandler.init(config, in_container)
    if not in_container:
        return (config["host"], int(config["port"]))
    return None

#========================================
def application(environ, start_response):
    return HServHandler.request(environ, start_response)

#========================================
if __name__ == '__main__':
    logging.basicConfig(level = 0)
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = "anfisa.json"

    from wsgiref.simple_server import make_server, WSGIRequestHandler

    #========================================
    class _LoggingWSGIRequestHandler(WSGIRequestHandler):
        def log_message(self, format, *args):
            logging.info(("%s - - [%s] %s\n" %
                (self.client_address[0], self.log_date_time_string(),
                format % args)).rstrip())

    #========================================
    host, port = setupHServer(config_file, False)
    httpd = make_server(host, port, application,
        handler_class = _LoggingWSGIRequestHandler)
    logging.info("HServer listening %s:%d" % (host, port))
    httpd.serve_forever()
else:
    logging.basicConfig(level = 10)
    setupHServer("./anfisa.json", True)