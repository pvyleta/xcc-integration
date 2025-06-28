#!/usr/bin/env python3
"""Mock XCC controller server for testing."""

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from aiohttp import web, web_request
from aiohttp.web_response import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class XCCMockServer:
    """Mock XCC controller server."""
    
    def __init__(self):
        self.sessions = {}
        self.mock_data_dir = Path("mock_data")
        self.current_values = self._load_mock_values()
        
    def _load_mock_values(self) -> dict:
        """Load mock values from JSON file."""
        values_file = self.mock_data_dir / "current_values.json"
        if values_file.exists():
            with open(values_file) as f:
                return json.load(f)
        return {}
    
    def _save_mock_values(self):
        """Save current values to JSON file."""
        values_file = self.mock_data_dir / "current_values.json"
        values_file.parent.mkdir(exist_ok=True)
        with open(values_file, 'w') as f:
            json.dump(self.current_values, f, indent=2)
    
    async def handle_login_xml(self, request: web_request.Request) -> Response:
        """Handle LOGIN.XML request."""
        session_id = "mock_session_" + str(hash(request.remote))[-8:]
        
        response = Response(
            text='<?xml version="1.0" encoding="UTF-8"?><LOGIN></LOGIN>',
            content_type='text/xml'
        )
        response.set_cookie('SoftPLC', session_id)
        
        logger.info(f"Login XML requested, session: {session_id}")
        return response
    
    async def handle_login_create(self, request: web_request.Request) -> Response:
        """Handle login creation."""
        data = await request.post()
        username = data.get('USER', '')
        password_hash = data.get('PASS', '')
        
        # Get session from cookie
        session_id = request.cookies.get('SoftPLC', '')
        
        # Validate credentials (mock validation)
        expected_hash = hashlib.sha1(f"{session_id}xcc".encode()).hexdigest()
        
        if username == 'xcc' and password_hash == expected_hash:
            self.sessions[session_id] = {'authenticated': True, 'user': username}
            logger.info(f"Authentication successful for session {session_id}")
            return Response(text="OK")
        else:
            logger.warning(f"Authentication failed for session {session_id}")
            return Response(text="FAIL", status=401)
    
    async def handle_xml_page(self, request: web_request.Request) -> Response:
        """Handle XML page requests."""
        page_name = request.match_info['page']
        session_id = request.cookies.get('SoftPLC', '')
        
        # Check authentication
        if session_id not in self.sessions or not self.sessions[session_id].get('authenticated'):
            return Response(text="<LOGIN></LOGIN>", content_type='text/xml', status=401)
        
        # Load mock XML data
        xml_file = self.mock_data_dir / page_name
        if xml_file.exists():
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace placeholders with current values
            for field, value in self.current_values.items():
                content = content.replace(f"{{{{ {field} }}}}", str(value))
            
            logger.info(f"Serving {page_name} for session {session_id}")
            return Response(text=content, content_type='text/xml')
        else:
            logger.warning(f"Page {page_name} not found")
            return Response(text="Page not found", status=404)
    
    async def handle_set_value(self, request: web_request.Request) -> Response:
        """Handle setting parameter values."""
        data = await request.post()
        param = data.get('param', '')
        value = data.get('value', '')
        
        session_id = request.cookies.get('SoftPLC', '')
        
        # Check authentication
        if session_id not in self.sessions or not self.sessions[session_id].get('authenticated'):
            return Response(text="Unauthorized", status=401)
        
        # Update value
        if param:
            self.current_values[param] = value
            self._save_mock_values()
            logger.info(f"Set {param} = {value}")
            return Response(text="OK")
        else:
            return Response(text="Invalid parameter", status=400)
    
    async def handle_index(self, request: web_request.Request) -> Response:
        """Handle index page."""
        return Response(text="""
        <html>
        <head><title>XCC Mock Controller</title></head>
        <body>
        <h1>XCC Mock Controller</h1>
        <p>This is a mock XCC controller for testing the Home Assistant integration.</p>
        <h2>Available Pages:</h2>
        <ul>
            <li><a href="/stavjed.xml">stavjed.xml</a></li>
            <li><a href="/STAVJED1.XML">STAVJED1.XML</a></li>
            <li><a href="/okruh.xml">okruh.xml</a></li>
            <li><a href="/OKRUH10.XML">OKRUH10.XML</a></li>
            <li><a href="/tuv1.xml">tuv1.xml</a></li>
            <li><a href="/TUV11.XML">TUV11.XML</a></li>
        </ul>
        <h2>Current Values:</h2>
        <pre>{}</pre>
        </body>
        </html>
        """.format(json.dumps(self.current_values, indent=2)), content_type='text/html')

def create_app():
    """Create the web application."""
    server = XCCMockServer()
    app = web.Application()
    
    # Routes
    app.router.add_get('/', server.handle_index)
    app.router.add_get('/LOGIN.XML', server.handle_login_xml)
    app.router.add_post('/RPC/WEBSES/create.asp', server.handle_login_create)
    app.router.add_get('/{page:.+\\.xml}', server.handle_xml_page)
    app.router.add_get('/{page:.+\\.XML}', server.handle_xml_page)
    app.router.add_post('/set_value', server.handle_set_value)
    
    return app

async def main():
    """Run the mock server."""
    app = create_app()
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("XCC Mock Server started on http://0.0.0.0:8080")
    
    # Keep running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
