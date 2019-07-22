# uWSGI howto

### Installing uWSGI
uWSGI does not work out of the box with websockets.

When installing uWSGI with ```pip```, it will compile a wheel. During compile time it will check if compile-time 
dependencies, such as ssl, exist, and if so, will compile support for that into ```uwsgi```. This means
that if those dependencies are not present, support for those extensions won't be available.

To get uWSGI running for the mapeditor, make sure the following dependencies are available before
```uwsgi``` is installed:

- ```libpcre3``` 
- ```libpcre3-dev```
- ```libz-dev```
- ```libssl-dev```, especially this one is required for websockets

When these are present, installing ```uwsgi``` using ```pip install uwsgi``` should work.
If it is already installed, uninstall it first and use the following command to force
the installation by ```pip```:

```UWSGI_PROFILE_OVERRIDE=ssl=true pip3.7 install uwsgi -Iv --no-cache-dir```

The ```-v``` option shows some debug information at the end of the compilation process for the wheel
and allows you to verify that e.g. SSL support is compiled in.


### Scaling with uWSGI and socket.io
uWSGI allows you to spawn multiple processes and threads to scale the application
Unfortunately, threads cannot be used when using ```gevent```, as that has its own 
mechanism to do asynchronous messaging (this is also the reason why websockets perform 
better than XMLHttpRequests (xhr) using long polling).

Unfortunately, multiple processes can also not be used because that does not work together with Socket.IO. 
If you do multiple processes: a MapEditor webpage load will be spread among the processes, resulting into multiple 
socket.io calls while we expect them to be synchronous as they share a single session. 
This also means that the ESDL is concurrently updated/queried.
This means that there is no 'sticky session'. Socket.IO has support for message-queues to share session information
but that setup is quite complicated. (see https://flask-socketio.readthedocs.io/en/latest/#using-multiple-workers)

The  alternative is to scale the Mapeditor itself, e.g. start several instances and load-balance them by e.g. Nginx.
