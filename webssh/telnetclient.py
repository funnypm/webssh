import logging
import socket
import time
import telnetlib


class TelnetSocket:
    """Telnet socket wrapper that mimics SSH channel interface"""
    
    def __init__(self, telnet_obj):
        self.telnet = telnet_obj
        self.closed = False
    
    def recv(self, bufsize):
        """Receive data from telnet"""
        try:
            data = self.telnet.read_very_eager()
            return data
        except EOFError:
            self.closed = True
            return b''
        except Exception as e:
            logging.error('Telnet recv error: {}'.format(e))
            self.closed = True
            return b''
    
    def send(self, data):
        """Send data to telnet"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            self.telnet.write(data)
            return len(data)
        except Exception as e:
            logging.error('Telnet send error: {}'.format(e))
            self.closed = True
            return 0
    
    def fileno(self):
        """Get socket file descriptor"""
        try:
            return self.telnet.get_socket().fileno()
        except Exception as e:
            logging.error('Telnet fileno error: {}'.format(e))
            return -1
    
    def setblocking(self, flag):
        """Set blocking mode"""
        try:
            sock = self.telnet.get_socket()
            sock.setblocking(flag)
        except Exception as e:
            logging.error('Telnet setblocking error: {}'.format(e))
    
    def close(self):
        """Close telnet connection"""
        if not self.closed:
            try:
                self.telnet.close()
            except Exception as e:
                logging.error('Telnet close error: {}'.format(e))
            self.closed = True
    
    def resize_pty(self, *args, **kwargs):
        """Telnet doesn't support pty resizing"""
        pass


class TelnetClient:
    """Telnet client implementation with SSH-like interface"""
    
    def __init__(self):
        self.telnet = None
        self.connected = False
        self.timeout = 10
        self.username = None
        self.password = None
    
    def connect(self, hostname, port, username, password, pkey=None, timeout=10, *args, **kwargs):
        """
        Connect to Telnet server
        
        Args:
            hostname: server hostname or IP
            port: server port (default 23)
            username: login username
            password: login password
            pkey: ignored (for SSH compatibility)
            timeout: connection timeout
        """
        self.timeout = timeout
        self.username = username
        self.password = password
        
        logging.info('Connecting to telnet {}:{}'.format(hostname, port))
        
        try:
            self.telnet = telnetlib.Telnet(hostname, port, timeout=timeout)
            self.connected = True
            
            # Wait for server greeting
            time.sleep(0.5)
            
            # Try to read initial banner/prompt
            try:
                banner = self.telnet.read_very_eager()
                if banner:
                    logging.debug('Telnet banner: {}'.format(banner[:100]))
            except Exception as e:
                logging.debug('Error reading banner: {}'.format(e))
            
            # Send username if provided
            if username:
                self.telnet.write(username.encode('utf-8') + b'\r\n')
                time.sleep(0.3)
            
            # Send password if provided
            if password:
                self.telnet.write(password.encode('utf-8') + b'\r\n')
                time.sleep(0.3)
            
            logging.info('Telnet connected to {}:{}'.format(hostname, port))
            
        except socket.timeout:
            raise ValueError('Telnet connection timeout to {}:{}'.format(hostname, port))
        except socket.error as e:
            raise ValueError('Unable to connect to {}:{} - {}'.format(hostname, port, str(e)))
        except Exception as e:
            raise ValueError('Telnet connection failed: {}'.format(str(e)))
    
    def invoke_shell(self, term='xterm', *args, **kwargs):
        """
        Invoke shell and return channel-like object
        
        Args:
            term: terminal type (ignored for Telnet)
        
        Returns:
            TelnetSocket wrapper
        """
        if not self.connected:
            raise RuntimeError('Not connected')
        
        return TelnetSocket(self.telnet)
    
    def close(self):
        """Close Telnet connection"""
        if self.telnet:
            try:
                self.telnet.close()
            except Exception as e:
                logging.error('Error closing telnet connection: {}'.format(e))
            self.connected = False
    
    def exec_command(self, command, *args, **kwargs):
        """Not supported for Telnet"""
        raise NotImplementedError('exec_command is not supported for Telnet')
