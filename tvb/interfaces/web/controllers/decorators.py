# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2017, Baycrest Centre for Geriatric Care ("Baycrest") and others
#
# This program is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with this
# program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Decorators for Cherrypy exposed methods are defined here.

.. moduleauthor:: Mihai Andrei <mihai.andrei@codemart.ro>
"""
import numpy
import os
import json
import cherrypy
import cProfile
from datetime import datetime
from functools import wraps
from genshi.template import TemplateLoader
from tvb.basic.profile import TvbProfile
from tvb.basic.logger.builder import get_logger
from tvb.core.utils import TVBJSONEncoder
from tvb.interfaces.web.controllers import common

# some of these decorators could be cherrypy tools

_LOGGER_NAME = "tvb.interface.web.controllers.decorators"


def using_template(template_name):
    """
    Decorator that renders a template
    """
    template_path = os.path.join(TvbProfile.current.web.TEMPLATE_ROOT, template_name + '.html')

    def dec(func):

        @wraps(func)
        def deco(*a, **b):
            template_dict = func(*a, **b)
            if not TvbProfile.current.web.RENDER_HTML:
                return template_dict

            ### Generate HTML given the path to the template and the data dictionary.
            loader = TemplateLoader()
            template = loader.load(template_path)
            stream = template.generate(**template_dict)
            return stream.render('xhtml')

        return deco
    return dec


def jsonify(func):
    """
    Decorator to wrap all JSON calls, and log on server in case of an exception.
    """

    @wraps(func)
    def deco(*a, **b):
        result = func(*a, **b)
        return json.dumps(result, cls=TVBJSONEncoder)

    return deco


def ndarray_to_http_binary(func):
    """
    Decorator to wrap calls that return numpy arrays. It serializes them as binary http response
    """
    @wraps(func)
    def deco(*a, **b):
        x = func(*a, **b)
        if not isinstance(x, numpy.ndarray):
            raise ValueError('Datatype attribute must be an ndarray for binary transport not %s' % type(x) )

        # map some unsupported dtypes to supported ones
        if x.dtype == numpy.int64:
            x = numpy.asarray(x, dtype=numpy.int32)

        if x.dtype not in [numpy.float32, numpy.float64, numpy.int32]:
            raise ValueError('Datatype not supported by binary transport %s' % x.dtype)

        x = numpy.ascontiguousarray(x)
        cherrypy.response.headers["Content-Type"] = "application/x.ndarray"
        cherrypy.response.headers["Content-Length"] = x.nbytes
        cherrypy.response.headers["X-Array-Shape"] = str(x.shape)
        cherrypy.response.headers["X-Array-Type"] = str(x.dtype)

        return x.tostring()

    return deco


def handle_error(redirect):
    """
    If `redirect` is true(default) all errors will generate redirects.
    Generic errors will redirect to the error page. Authentication errors to login pages.
    If `redirect` is false redirect will be converted to errors http 500
    All errors are logged
    Redirect false is used by ajax calls
    """
    # this offers some context if not already present in the logs
    # def _reql():
    #     return ' when calling \n' + cherrypy.request.request_line

    def dec(func):
        @wraps(func)
        def deco(*a, **b):
            try:

                return func(*a, **b)

            except common.NotAllowed as ex:
                log = get_logger(_LOGGER_NAME)
                log.error(str(ex))

                if redirect:
                    common.set_error_message(str(ex))
                    raise cherrypy.HTTPRedirect(ex.redirect_url)
                else:
                    raise cherrypy.HTTPError(ex.status, str(ex))

            except cherrypy.HTTPRedirect as ex:
                if redirect:
                    raise
                else:
                    log = get_logger(_LOGGER_NAME)
                    log.warn('Redirect converted to error: ' + str(ex))
                    # should we do this? Are browsers following redirects in ajax?
                    raise cherrypy.HTTPError(500, str(ex))

            except Exception:
                log = get_logger(_LOGGER_NAME)
                log.exception('An unexpected exception appeared')

                if redirect:
                    # set a default error message if one has not been set already
                    if not common.has_error_message():
                        common.set_error_message("An unexpected exception appeared. Please check the log files.")
                    raise cherrypy.HTTPRedirect("/tvb?error=True")
                else:
                    raise

        return deco
    return dec


def check_user(func):
    """
    Decorator to check if a user is logged before accessing a controller method.
    """

    @wraps(func)
    def deco(*a, **b):
        if hasattr(cherrypy, common.KEY_SESSION):
            if common.get_logged_user():
                return func(*a, **b)
        raise common.NotAuthenticated('Login Required!', redirect_url='/user')

    return deco


def check_admin(func):
    """
    Decorator to check if a user is administrator before accessing a controller method
    """
    @wraps(func)
    def deco(*a, **b):
        if hasattr(cherrypy, common.KEY_SESSION):
            user = common.get_logged_user()
            if user is not None and user.is_administrator() or TvbProfile.is_first_run():
                return func(*a, **b)
        raise common.NotAuthenticated('Only Administrators can access this application area!', redirect_url='/tvb')

    return deco


def context_selected(func):
    """
    Decorator to check if a project is currently selected.
    """

    @wraps(func)
    def deco(*a, **b):
        if hasattr(cherrypy, common.KEY_SESSION):
            if common.KEY_PROJECT in cherrypy.session:
                return func(*a, **b)
        raise common.NotAllowed('You should first select a Project!', redirect_url='/project/viewall')

    return deco


def settings(func):
    """
    Decorator to check if a the settings file exists before allowing access
    to some parts of TVB.
    """

    @wraps(func)
    def deco(*a, **b):
        if not TvbProfile.is_first_run():
            return func(*a, **b)
        raise common.NotAllowed('You should first set up tvb', redirect_url='/settings/settings')

    return deco


def expose_page(func):
    """
    Equivalent to
    @cherrypy.expose
    @handle_error(redirect=True)
    @using_template2('base_template')
    @check_user
    """
    func = check_user(func)
    func = using_template('base_template')(func)
    func = handle_error(redirect=True)(func)
    func = cherrypy.expose(func)
    return func


def expose_fragment(template_name):
    """
    Equivalent to
    @cherrypy.expose
    @handle_error(redirect=False)
    @using_template2(template)
    @check_user
    """
    def deco(func):
        func = check_user(func)
        func = using_template(template_name)(func)
        func = handle_error(redirect=False)(func)
        func = cherrypy.expose(func)
        return func

    return deco


def expose_json(func):
    """
    Equivalent to
    @cherrypy.expose
    @handle_error(redirect=False)
    @jsonify
    @check_user
    """
    func = check_user(func)
    func = jsonify(func)
    func = handle_error(redirect=False)(func)
    func = cherrypy.expose(func)
    return func


def expose_numpy_array(func):
    func = check_user(func)
    func = ndarray_to_http_binary(func)
    func = handle_error(redirect=False)(func)
    func = cherrypy.expose(func)
    return func


def profile_func(func):
    def wrapper(*args, **kwargs):
        log = get_logger(_LOGGER_NAME)
        profile_file = func.__name__ + datetime.now().strftime("%d-%H-%M-%S.%f") + ".profile"
        log.info("profiling function %s. Profile stored in %s" % (func.__name__, profile_file))
        prof = cProfile.Profile()
        ret = prof.runcall(func, *args, **kwargs)
        prof.dump_stats(profile_file)
        return ret

    return wrapper


def _profile_sqlalchemy(func):
    """
    Count the number of db queries. Note that this implementation should be used
    for debugging only and on few functions. Due to a limitation in sqlalchemy 1.7 it leaks events
    """
    from sqlalchemy import event
    from sqlalchemy.engine.base import Engine

    log = get_logger(_LOGGER_NAME)

    def wrapper(*args, **kwargs):
        d = [0]

        def _after_cursor_execute(conn, cursor, stmt, params, context, execmany):
            d[0] += 1

        event.listen(Engine, "after_cursor_execute", _after_cursor_execute)
        ret = func(*args, **kwargs)
        # event.remove(Engine, "after_cursor_execute", _after_cursor_execute)
        log.info("Queries issues by function %s, id %s : %s" % (func.__name__, id(func), d[0]))
        return ret

    return wrapper
