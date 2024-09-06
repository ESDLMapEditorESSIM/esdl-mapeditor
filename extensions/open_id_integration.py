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


from authlib.integrations.flask_client import FlaskOAuth2App
from authlib.jose import JsonWebKey, jwt, JWTClaims
from authlib.oauth2.rfc6749 import OAuth2Token
from authlib.oidc.core import UserInfo
from flask import g, session
from flask_oidc import OpenIDConnect
from flask_oidc.model import User


class OpenIDIntegration:
    """
    This class adds some support functions to integrate with the new flask_oidc (>2.0.0) and Authlib libraries,
    and create a cleaner API to get the right information from the tokens
    """

    def __init__(self, oidc: OpenIDConnect):
        self.oidc = oidc

    def get_access_token(self) -> str:
        """
        retrieve access token in base64 string
        :return: access token in base64 string
        """
        return self.oidc.get_access_token()

    def get_refresh_token(self) -> str:
        """
        return refresh token in base64 string
        :return: access token in base64 string
        """
        return self.oidc.get_refresh_token()

    def get_id_token(self) -> str:
        """
        return id token in base64 string
        :return: id token in base64 string
        """
        token: OAuth2Token = session.get("oidc_auth_token", {})
        return token["id_token"]

    def get_full_oauth_token(self) -> OAuth2Token | None:
        token: OAuth2Token = session.get("oidc_auth_token", {})
        if token:
            return token
        else:
            return None

    def get_parsed_jwt(self) -> JWTClaims:
        """
        Parse the id token (text) from the IDP into JWTClaims (dict)
        These claims contain more information than available in the user's profile
        :param session: session containing oidc_auth_token
        :return: dictionary with parsed JWT Claims from the Id token
        """

        token = session.get("oidc_auth_token")
        oauth_app: FlaskOAuth2App = self.oidc.oauth.oidc
        if "userinfo" in token:
            # use cached userinfo until token is refreshed (then userinfo is removed from token in
            # Authlib's FlaskOAuth2App)
            return token["userinfo"]

        def load_key(header, _):
            jwk_set = JsonWebKey.import_key_set(oauth_app.fetch_jwk_set())
            try:
                return jwk_set.find_by_kid(header.get("kid"))
            except ValueError:
                # re-try with new jwk set
                jwk_set = JsonWebKey.import_key_set(oauth_app.fetch_jwk_set(force=True))
                return jwk_set.find_by_kid(header.get("kid"))

        parsed_token = jwt.decode(token["id_token"], key=load_key)
        # we could also validate the token here, but we only parse here.
        # See FlaskOAuth2App bottom of the file

        if "userinfo" not in token:
            # cache user info, so we don't have to decode for each request
            token["userinfo"] = parsed_token

        return parsed_token

    def get_userinfo(self) -> UserInfo:
        """

        :return: the OpenIDConnect user info of this user (class extending a dict)
        """
        token: OAuth2Token = session.get("oidc_auth_token")
        return self.oidc.oauth.oidc.userinfo(token=token)

    def get_user(self) -> User:
        """
        Returns the User information
        :return: user information as User class of flask-oidc
        """
        user: User = g.oidc_user
        return user

    def get_email(self) -> str:
        """
        :return: the email address of the current user
        """
        user: User = g.oidc_user
        user_email = user.profile.get("email")
        return user_email

    def get_user_profile(self) -> dict:
        """

        :return: a dict with the user profile
        """
        user: User = g.oidc_user
        return user.profile

    def user_loggedin(self) -> bool:
        """
        Represents whether the user is currently logged in.

        :return: Whether the user is logged in with Flask-OIDC.
        """
        return session.get("oidc_auth_token") is not None
