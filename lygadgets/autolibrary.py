''' This module converts pcells of any type into KLayout-style PCells

    All of these things are not specific to any technology.
    Eventually, this module could be part of an independent PDK specification package.

    It is a bad idea to have this "python" directory permanently because
    this is a technology specification package, not a functional codebase.
'''
# Todo: handle TypeList and TypeLayer arguments
# Going to be difficult to handle: arguments that are other phidl.Device objects or functions

from lygadgets import pya
import os
from inspect import signature
from lygadgets import anyCell_to_anyCell

def cellname_to_kwargs(cellname):
    ''' Converts the naming convention for parameter-based cell naming back into a dict of kwargs '''
    # this function has not been tested yet
    func_kwargs = dict()
    func_name, paramstr = cellname.split('__')  # double underscore has been sanitized
    for oneparamstr in paramstr.split('_'):  # todo: unsanitize _ and =
        name, val = oneparamstr.split('=')
        try:
            val = int(val)
        except ValueError:
            try:
                val = float(val)
            except ValueError:
                pass
        func_kwargs[name] = val
    return func_kwargs


def pytype_to_PCelltype(arg_type):
    ''' Maps builtin python types to the corresponding types of the PCellDeclarationHelper class
    '''
    # this has been tested only with floats so far
    if issubclass(arg_type, int):
        return pya.PCellDeclarationHelper.TypeInt
    if issubclass(arg_type, float):
        return pya.PCellDeclarationHelper.TypeDouble
    if issubclass(arg_type, (list, tuple)):
        return pya.PCellDeclarationHelper.TypeList
    if issubclass(arg_type, str):
        return pya.PCellDeclarationHelper.TypeString
    if issubclass(arg_type, bool):
        return pya.PCellDeclarationHelper.TypeBoolean
    if issubclass(arg_type, NoneType):
        return pya.PCellDeclarationHelper.TypeNone


def my_argspec(function):
    ''' Extracts the arguments and keyword arguments from any callable object.
        The dictionary of kwargs is returned with values reflecting their default arguments
    '''
    func_signature = signature(function)
    args = list()
    kwargs = dict()
    for key, param in func_signature.parameters.items():
        kwargs[key] = param.default
    return args, kwargs


# protect against missing pya
if pya is None:
    class WrappedPCell(object):
        def __init__(self, *args, **kwargs):
            raise AttributeError('WrappedPCell requires a working installation of klayout python package')
    class WrappedLibrary(object):
        def __init__(self, *args, **kwargs):
            raise AttributeError('WrappedLibrary requires a working installation of klayout python package')
else:
    class WrappedPCell(pya.PCellDeclarationHelper):
        ''' Wraps a non-klayout PCell as a klayout PCell.
            The pcell is here defined as a function with arguments.
            When produce_impl is called, the cell geometry is compiled and added to this instance's cell.

            The transfer of external pcell geometry is done through a temporary gds file.

            I think this is not specific to phidl implementation. It just needs some function.
            Oh wait, yes it is (barely) because of write_gds.
        '''
        generating_function = None

        def kwargs_to_params(self):
            ''' Extracts the arguments of the generating_function and registers them as params of this object
                If it is a keyword argument, the default type is detected and value added as default
            '''
            def kwarg_to_param(key, default=None):
                self.param(key, pytype_to_PCelltype(type(default)), key, default=default)
            args, kwargs = my_argspec(self.generating_function)
            for arg in args:
                kwarg_to_param(arg)
            for key, default in kwargs.items():
                kwarg_to_param(key, default)

        def params_to_kwargs(self):
            ''' Inverse of kwargs_to_params. Converts the parameters of this instance and their chosen values
                back into arguments that can be sent to the generating_function.
            '''
            # todo: handle non-keyword args
            all_args = list()
            all_kwargs = dict()
            for pdecl, pval in zip(self.get_parameters(), self.get_values()):
                all_kwargs[pdecl.name] = pval
            return all_args, all_kwargs

        def __init__(self, generating_function):
            self.generating_function = generating_function
            super().__init__()
            self.kwargs_to_params()

        def display_text_impl(self):
            ''' Produces a string that includes all of the parameters. This means it is unique for identical cells.
                We assume that the pcells are functional in the sense that identical parameters yield identical geometry.
                In this way, different pcell instances with the same arguments are correctly identified as the same cell.
            '''
            text = self.generating_function.__name__ + '_'
            for pdecl, pval in zip(self.get_parameters(), self.get_values()):
                # sanitize _'s and ='s
                if isinstance(pval, str):
                    pval.replace('_', '[_]')
                    pval.replace('=', '[=]')
                text += '_{}={}'.format(pdecl.name, pval)
            return text

        def produce_impl(self):
            ''' Creates a fixed cell instance based on the previously specified parameters
            '''
            # Produce the geometry
            args, kwargs = self.params_to_kwargs()
            phidl_Device = self.generating_function(*args, **kwargs)
            # Convert phidl.Device to pya.Cell - just geometry
            anyCell_to_anyCell(phidl_Device, self.cell)
            # Transfer other data (ports, metadata, CML files, etc.)
            pass  # TODO


    class WrappedLibrary(pya.Library):
        ''' An abstract library consisting of pya PCells that are
            based on function calls that possibly involve other languages (specified in all_funcs_to_wrap)
            The names of the PCells will end up being the same as the names of the functions.

            Initializing the library registers it in klayout's repository of libraries.

            To subclass this class, no extra methods are needed.
            Just override the class attributes.
        '''
        tech_name = None
        all_funcs_to_wrap = None
        description = None

        def __init__(self):
            if self.tech_name is None or self.all_funcs_to_wrap is None:
                raise NotImplementedError('WrappedLibrary must be subclassed.')

            print("Initializing '%s' Library." % self.tech_name)

            # Not doing fixed GDS in this Library

            # Create all the new klayout-format PCells
            for func in self.all_funcs_to_wrap:
                self.layout().register_pcell(func.__name__, WrappedPCell(func))  # generic version

            self.register(self.tech_name)

            if int(pya.Application.instance().version().split('.')[1]) > 24:
                # KLayout v0.25 introduced technology variable:
                self.technology = self.tech_name
