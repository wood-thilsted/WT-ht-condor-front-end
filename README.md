# registration

This is the web application for Open Science Pool token registration

## Structure

The web app is a [Flask](https://flask.palletsprojects.com/) app.
The core app is created in an 
["application factory"](https://flask.palletsprojects.com/en/1.1.x/patterns/appfactories/)
in `registry/app.py`,
and it hooks together 
[blueprints](https://flask.palletsprojects.com/en/1.1.x/tutorial/views/)
found in some of the subdirectories of `registry/`.

Blueprints:
- `index` - landing page, "about" page, etc.
- `account` - handles user accounts. We don't quite have registration because we use CILogon, but this is where you can go to see (for example) your contact email.
- `signup` - handles forms for users to register themselves and their data sources.
- `connect` - provides instructions for users to install and connect their data sources.
- `token` - handles the server side of the token workflow when connecting a new data source.

Each blueprint has its own `static` and `templates` directories, and there
are also "global" `static` and `templates` directories that sit next to
`app.py`. These directories are for:
- `static` - for static assets like `.css` files, images, etc.
- `templates` - for [Jinja HTML templates](https://flask.palletsprojects.com/en/1.1.x/templating/).

### `register.py`

This repository also includes `register.py`, the client-side script for
getting a token for a new data source.
It's stored here because it talks to the `token` blueprint, and therefore
needs to stay in sync with it.

## Development

To run the registration server locally, build and run the testing container image:

1.  Build the container image:

        docker build -t os-registry-test -f Dockerfile.testing .

1.  Copy example configuration required by the registry server:

        cp examples/config.py examples/humans.ini .

1.  Start the local registry:

        docker run --rm -it -v ${PWD}:/srv -p 8443:443 os-registry-test

1.  Access the local registry in your browser by accessing <https://localhost:8443>

Note that changes to files copied into the container image (e.g. `COPY` lines in `Dockerfile.testing`) will require
a rebuild of the container image.

## Installation

Clone the repository to wherever you would like to serve the application from
(e.g., `/var/www/registration`).

Example/template Apache configuration:
```
<VirtualHost *:443>
  ServerName htpheno-cm.chtc.wisc.edu
  ServerAdmin htcondor-inf@cs.wisc.edu

  # This is the OIDC callback path
  <Location "/callback">
    <RequireAny>
      Require valid-user
    </RequireAny>
    AuthType openid-connect
  </Location>

  ## Logging
  ErrorLog "/var/log/httpd/local_default_ssl_error_ssl.log"
  LogLevel info
  ServerSignature Off
  CustomLog "/var/log/httpd/local_default_ssl_access_ssl.log" combined 

  ## SSL directives
  SSLEngine on
  SSLCertificateFile      "/var/www/hostcert.pem"
  SSLCertificateKeyFile   "/var/www/hostkey.pem"
  SSLCertificateChainFile "/var/www/hostcert.pem"

  ## WSGI configuration
  WSGIDaemonProcess Registration display-name=Registration group=condor processes=2 threads=25 user=condor
  WSGIProcessGroup Registration
  WSGIScriptAlias / "/var/www/registration/wsgi.py"

  ## OIDC configuration
  OIDCProviderMetadataURL https://cilogon.org/.well-known/openid-configuration
  OIDCClientID cilogon:/client_id/<secret>
  OIDCClientSecret <secret>

  OIDCRedirectURI https://htpheno-cm.chtc.wisc.edu/callback

  # Used to encrypt the session cookie and the local cache.
  OIDCCryptoPassphrase <secret>

  # Control the information in the returned token.
  OIDCScope  "openid email org.cilogon.userinfo"

  # The value of this scope is used as the username in the environment
  # variables provided to WSGI.
  OIDCRemoteUserClaim  eppn

</VirtualHost>
```

By default we "protect" everything under `/` with OIDC.
Some pages should be "public", i.e., unprotected 
(right now, these are the 
"index" and "about" pages, and anything under `/static`, 
so that static assets can always be served).
This is managed by Apache, not the webapp.
Example configuration below:

```
  <Location "/">
    <RequireAny>
      Require valid-user
    </RequireAny>
    AuthType openid-connect
  </Location>

  <LocationMatch "^/$">
    <RequireAny>
      Require all granted
    </RequireAny>
    AuthType none
  </LocationMatch>

  <Location "/about">
    <RequireAny>
      Require all granted
    </RequireAny>
    AuthType none
  </Location>

  <Location "/static">
    <RequireAny>
      Require all granted
    </RequireAny>
    AuthType none
  </Location>
```


## Configuration

Configuration options will be read out of a file named `config.py`, placed at the
root of the repository, next to this `README.md`. The file should contain
global variables with names matching the configuration options described below,
like
```python
USER_ID_ENV_VAR = "REMOTE_USER"
```

### Required

These configuration options **must** be set.
They do not have defaults.

* `COLLECTOR` - The Open Science pool collector hostname.
* `SERVER_NAME` - The hostname of the host server.
* `OIDC_REDIRECT_URI` - The URI for the OIDC redirect.
* `USER_ID_ENV_VAR` - The request environment variable that holds the user's identity.
* `HUMANS_FILE` - The path to the file that contains information on humans.
* `ADMIN_EMAILS` - The email addresses that will receive mail when users sign up, like `ADMIN_EMAILS = "Foo Bar <foobar@university.edu>, Wiz Bang <wizbang@organization.org>"`.
* `SUPPORT_EMAIL` - The email address to display for users to send support questions to.

### Optional

* `CONDOR_TOKEN_REQUEST_LIST` - The path to the `condor_token_request_list` executable. By default, discover it on `$PATH`.
* `CONDOR_TOKEN_REQUEST_APPROVE` - The path to the `condor_token_request_approve` executable. By default, discover it on `$PATH`.
