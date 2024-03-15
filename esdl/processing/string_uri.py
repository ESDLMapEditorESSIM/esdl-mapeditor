#  This work is based on original code developed and copyrighted by TNO 2020.
#  Subsequent contributions are licensed to you by the developers of such code and are
#  made available to the Project under one or several contributor license agreements.
#
#  This work is licensed to you under the Apache License, Version 2.0.
#  You may obtain a copy of the license at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Contributors:
#      TNO         - Initial implementation
#  Manager:
#      TNO

from io import BytesIO

from pyecore.resources import URI


class StringURI(URI):
    """
    A subclass of URI, that also contains the contents of the resource in memory. This
    can be provided in the text parameter. It implements the proper interface for
    reading the resource, so that the resource set can read in the energy system from
    memory.
    """
    def __init__(self, uri: str, text=None):
        """
        Creates a new URI that can contain a string.
        This class is used to convert/parse ESDL strings to resources and classes.
        Parameters
        ----------
        uri The uri/filename that the created resource will have
        text String to parse and convert to
        """
        super(StringURI, self).__init__(uri)
        if text is not None:
            self.__stream = BytesIO(text.encode('UTF-8'))

    def getvalue(self):
        readbytes = self.__stream.getvalue()
        # somehow stringIO does not work, so we use BytesIO
        string = readbytes.decode('UTF-8')
        return string

    def create_instream(self):
        return self.__stream

    def create_outstream(self):
        self.__stream = BytesIO()
        return self.__stream

    def get_stream(self):
        return self.__stream

    def __repr__(self):
        return f"StringURI(uri={self.plain})"
