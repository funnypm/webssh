import logging
import socket
import time


class TelnetSocket:
    """Telnet socket wrapper that mimics SSH channel interface"""
    
    def __init__(self, sock):
        self.sock = sock
        self.closed = False
    
    def recv(self, bufsize):
        """Receive data from socket"""
        try:
            data = self.sock.recv(bufsize)
            return data
        except socket.timeout:
            return b''
        except Exception as e:
            logging.error('Telnet recv error: {}'.format(e))
            self.closed = True
            return b''
    
    def send(self, data):
        """Send data to socket"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')
            return self.sock.send(data)
        except Exception as e:
            logging.error('Telnet send error: {}'.format(e))
            self.closed = True
            return 0
    
    def fileno(self):
        """Get socket file descriptor"""
        return self.sock.fileno()
    
    def setblocking(self, flag):
        """Set blocking mode"""
        self.sock.setblocking(flag)
    
    def close(self):
        """Close socket"""
        if not self.closed:
            try:
                self.sock.close()
            except Exception as e:
                logging.error('Telnet close error: {}'.format(e))
            self.closed = True
    
    def resize_pty(self, *args, **kwargs):
        """Telnet doesn't support pty resizing"""
        pass


class TelnetClient:
    """Telnet client implementation with SSH-like interface"""
    
    def __init__(self):
        self.sock = None
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
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((hostname, port))
            self.connected = True
            
            # Wait for server greeting
            time.sleep(0.5)
            
            # Try to read initial banner/prompt
            try:
                self.sock.settimeout(1)
                banner = self.sock.recv(4096)
                logging.debug('Telnet banner: {}'.format(banner))
            except socket.timeout:
                pass
            finally:
                self.sock.settimeout(timeout)
            
            # Send username if provided
            if username:
                self.sock.send(username.encode() + b'\r\n')
                time.sleep(0.3)
            
            # Send password if provided
            if password:
                self.sock.send(password.encode() + b'\r\n')
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
        
        return TelnetSocket(self.sock)
    
    def close(self):
        """Close Telnet connection"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logging.error('Error closing telnet socket: {}'.format(e))
            self.connected = False
    
    def exec_command(self, command, *args, **kwargs):
        """Not supported for Telnet"""
        raise NotImplementedError('exec_command is not supported for Telnet')
