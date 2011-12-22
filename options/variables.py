
import os
import sys

import utils
import logging
import version

_Error = logging.Error

#//===========================================================================//
#//===========================================================================//

class Variables:
    
    def     __init__( self ):
        
        self.__dict__['__names_dict']   = {}
        self.__dict__['__ids_dict']     = {}
        self.__dict__['__env']          = None
        self.__dict__['__cache']        = {}
        self.__dict__['__overridden']   = None
    
    vars.ccflags.New( )
    
    #//-------------------------------------------------------//
    
    def     __add_to_dict( self, name, option, id = id ):
        self.__dict__['__names_dict'][ name ] = option
        self.__dict__['__ids_dict'].setdefault( id( option ), (option, []) )[1].append( name )
    
    #//-------------------------------------------------------//
    
    def     __find_option( self, name ):
        return self.__dict__['__names_dict'].get( name )
    
    #//-------------------------------------------------------//
    
    def     __add_option( self, name, value ):
        
        if not _is_option( value ):
            _Error( "Option '%s' is unknown and value '%s' is not an option" % (name,value) )
            #~ if _isSequence( value ):   is_list = 1
            #~ else:                      is_list = 0
            
            #~ value = StrOption( initial_value = value, is_list = is_list )   # use the default option type for unknown options
        
        self.__add_to_dict( name, value )
        
        value.SetOptions( self )
    
    #//-------------------------------------------------------//
    
    def     __set_option( self, name, value, update = 0, quiet = 0 ):
        
        option = self.__find_option( name )
        
        if option is None:
            if (not update) or (not quiet):
                self.__add_option( name, value )
        else:
            
            if option is value:
                return
            
            if update:
                option.Update( value )
            else:
                option.Set( value )
    
    #//-------------------------------------------------------//
    
    def     __get_option( self, name, exception_type = AttributeError ):
        option = self.__find_option( name )
        
        if option is None:
            raise exception_type( "Unknown option: '%s'" % (name) )
        
        return option
    
    #//-------------------------------------------------------//
    
    def     __list_options( self ):
        return self.__dict__['__names_dict'].iterkeys()
    
    #//-------------------------------------------------------//
    
    def     __setattr__(self, name, value):
        self.__set_option( name, value )
    
    #//-------------------------------------------------------//
    
    def     __getattr__( self, name ):
        return self.__get_option( name )
    
    #//-------------------------------------------------------//
    
    def     __setitem__( self, name, value ):
        self.__set_option( name, value )
        
    #//-------------------------------------------------------//
    
    def     __getitem__( self, name ):
        return self.__get_option( name, KeyError )
    
    #//-------------------------------------------------------//
    
    def     keys( self ):
        return self.__dict__['__names_dict'].keys()
    
    def     iterkeys( self ):
        return self.__dict__['__names_dict'].iterkeys()
    
    #//-------------------------------------------------------//
    
    def     has_key( self, key ):
        if self.__find_option( key ):
            return 1
        
        return 0
    
    #//-------------------------------------------------------//
    
    def     get( self, key, default = None ):
        value = self.__find_option( key )
        if value is None:
            return default
        
        return value
    
    #//-------------------------------------------------------//
    
    def     update( self, args, quiet = 1,
                    isDict = utils.isDict,
                    isString = utils.isString ):
        
        if isString( args ):
            filename = args
            args = {'options':self}
            execfile( filename, {}, args )
            
            if args['options'] is self:
                del args['options']
        
        if isDict( args ):
            set_option = self.__set_option
            
            for key, value in args.iteritems():
                set_option( key, value, update = 1, quiet = quiet )
        else:
            _Error( "Invalid argument: %s" % (str(args)) )

    #//-------------------------------------------------------//
    
    def     __iadd__(self, other ):
        
        self.update( other )
        
        return self
    
    #//-------------------------------------------------------//
    
    def     OptionNames( self, opt, id = id ):
        
        try:
            return self.__dict__['__ids_dict'][ id(opt) ][1]
        
        except KeyError:
            return [ None ]
    
    #//-------------------------------------------------------//
    
    def     __call__( self, **kw ):
        options = self.Clone()
        options.update( kw, quiet = 0 )
        
        return options
    
    #//-------------------------------------------------------//
    
    def     Clone( self, id = id ):
        
        options = Options()
        
        options.__dict__['__env'] = self.__dict__['__env']
        
        ids_dict = options.__dict__['__ids_dict']
        names_dict = options.__dict__['__names_dict']
        
        for opt, names  in  self.__dict__['__ids_dict'].itervalues():
            
            option = opt._clone( options )
            
            for name in names:
                names_dict[ name ] = option
            
            ids_dict[ id( option ) ] = ( option, names )
        
        return options
    
    #//-------------------------------------------------------//
    
    def     __nonzero__( self ):
        return len( self.__dict__['__names_dict'] )
    
    #//-------------------------------------------------------//
    
    def     If( self ):
        return _ConditionalOptions( self );
    
    #//-------------------------------------------------------//
    
    def     __repr__( self ):
        return "<AQL options>"
    
    def     __str__( self ):
        return str( self.__dict__['__names_dict'] )
    
    #//-------------------------------------------------------//
    
    def     Env( self ):
        return self.__dict__['__env']
    
    def     SetEnv( self, env ):
        self.__dict__['__env'] = env
    
    #//-------------------------------------------------------//
    
    def     Cache( self ):
        return self.__dict__['__cache']
    
    def     ClearCache( self ):
        self.__dict__['__cache'] = {}

#//===========================================================================//
#//===========================================================================//

def     _convert_value( option, value,
                        isSequence = utils.isSequence ):
    
    converted_value = option._convert_value( value )
    
    if isSequence(converted_value):
        _Error("Can't convert a sequence: %s to non-sequence option: '%s'" % (converted_value, option.Name()) )
    
    return converted_value

#//---------------------------------------------------------------------------//

class   _OptionValue:
    def     __init__( self, value, option ):
        
        name = value.Name()
        
        if name is None:
            _Error("Unknown option name. Can't use a value of the unknown option" )
        
        self.name = name
        
        if __debug__:
            _convert_value( option, value  )     # check the current value
        
    #//-------------------------------------------------------//
    
    def     Get( self, option, opt_current_value ):
        
        opt = option.options[ self.name ]
        
        if opt is option:
            return opt_current_value
        
        return _convert_value( option, opt )

#//---------------------------------------------------------------------------//

class   _SimpleValue:
    def     __init__( self, value, option, isSequence = utils.isSequence ):
        
        if isSequence( value ):
            _Error("Can't convert a sequence: %s to non-sequence option: '%s'" % (value, option.Name()) )
        
        if value is None:
            self.value  = None
        
        else:
            self.value = _convert_value( option, value )
    
    #//-------------------------------------------------------//
    
    def     Get( self, option, opt_current_value ):
        return self.value

#//---------------------------------------------------------------------------//

class   _Value:
    
    def     __init__( self, value, option ):
        
        if _is_option( value ):
            self.value = _OptionValue( value, option )
        
        else:
            self.value = _SimpleValue( value, option )
    
    #//-------------------------------------------------------//
    
    def     Get( self, option, opt_current_value ):
        return self.value.Get( option, opt_current_value )


#//===========================================================================//

def     _convert_list_values( option, value,
                             toSequence = utils.toSequence,
                             appendToList = utils.appendToList ):
    
    convert_value = option._convert_value
    
    values = []
    for v in toSequence( value ):
        appendToList( values, convert_value( v ) )
    
    return values

#//---------------------------------------------------------------------------//

class   _OptionListValue:
    def     __init__( self, value, option ):
        
        name = value.Name()
        
        if name is None:
            _Error("Unknown option name. Can't use a value of the unknown option" )
        
        self.name = name
        
        if __debug__:
            _convert_list_values( option, value.Value() )   # check the current value
        
    #//-------------------------------------------------------//
    
    def     Get( self, option, opt_current_value,
                 toSequence = utils.toSequence ):
        
        opt = option.options[ self.name ]
        
        if opt is option:
            return toSequence( opt_current_value )
        
        return _convert_list_values( option, opt.Value() )

#//---------------------------------------------------------------------------//

class   _SimpleListValue:
    def     __init__( self, value, option ):
        self.values = utils.toSequence( option._convert_value( value ) )
    
    #//-------------------------------------------------------//
    
    def     Get( self, option, opt_current_value ):
        return self.values

#//---------------------------------------------------------------------------//

class   _ValueList:
    
    def     __init__( self, values, option,
                      toSequence = utils.toSequence ):
        
        values = toSequence( values, option.shared_data['separator'] )
    
        self_values = []
        
        for v in values:
            
            if _is_option( v ):
                v = _OptionListValue( v, option )
            
            else:
                v = _SimpleListValue( v, option )
            
            self_values.append( v )
        
        self.values = self_values
    
    #//-------------------------------------------------------//
    
    def     Get( self, option, opt_current_value ):
        
        values = []
        
        for v in self.values:
            values += v.Get( option, opt_current_value )
        
        return values

#//===========================================================================//

def     _MakeValue( value, option, isinstance = isinstance ):
    
    if isinstance( value, ( _Value, _ValueList ) ):
        return value
    
    if option.shared_data['is_list']:       return _ValueList( value, option )
    else:                                   return _Value( value, option )

#//===========================================================================//
#//===========================================================================//

# All below condtions assumes that 'None' can be anyone

def     _lt( op, value1, value2 ):
    if value1 is None:  return 0
    return value1 <  value2.Get( op, value1 )

def     _le( op, value1, value2 ):
    if value1 is None:  return 1
    return value1 <= value2.Get( op, value1 )

def     _eq( op, value1, value2 ):
    if value1 is None:  return 1
    return value1 == value2.Get( op, value1 )

def     _ne( op, value1, value2 ):
    if value1 is None:  return 0
    return value1 != value2.Get( op, value1 )

def     _gt( op, value1, value2 ):
    if value1 is None:  return 0
    return value1 >  value2.Get( op, value1 )

def     _ge( op, value1, value2 ):
    if value1 is None:  return 1
    return value1 >= value2.Get( op, value1 )

#//-------------------------------------------------------//

def     _has( op, values1, values2 ):
    
    if __debug__:
        if not op.shared_data['is_list']:
            _Error( "Operation 'has' is not allowed for a non-sequence option (%s)" % (op.Name()) )
    
    for v in values2.Get( op, values1 ):
        if v not in values1:
            return 0
    
    return 1

#//-------------------------------------------------------//

def     _has_any( op, values1, values2 ):
    
    if __debug__:
        if not op.shared_data['is_list']:
            _Error( "Operation 'has' is not allowed for a non-sequence option (%s)" % (op.Name()) )
    
    for v in values2.Get( op, values1 ):
        if v in values1:
            return 1
    
    return 0

#//-------------------------------------------------------//

def     _one_of( op, value1, values2, len = len ):
    
    if __debug__:
        if op.shared_data['is_list']:
            _Error( "Operation 'one_of' is not allowed for a sequence option (%s)" % (op.Name()) )
    
    return value1 in values2.Get( op, value1 )

#//===========================================================================//

def     _always_true_condition( options, op, current_value ):
    return 1

#//===========================================================================//

class   _Condition:
    
    def     __init__( self, name, cond_function, value ):
        self.name = name
        self.cond_function = cond_function
        self.value =  value
    
    #//-------------------------------------------------------//
    
    def     __call__( self, options, op, current_value ):
        
        option = options[ self.name ]
        
        if option is not op:
            current_value = option.Value()
        
        return self.cond_function( option, current_value, self.value )

#//===========================================================================//
#//===========================================================================//

class   _ConditionalValue:
    
    def    __init__( self ):
        self.conditions = []
        self.value = None
        self.operation = None
    
    #//-------------------------------------------------------//
    
    def     Append( self, cond ):
        
        if isinstance( cond, _ConditionalValue ):
            self.conditions += cond.conditions
        
        else:
            if __debug__:
                if not callable( cond ):
                    _Error( "Condition should be callable object: condition( options )" )
            
            self.conditions.append( cond )
    
    #//-------------------------------------------------------//
    
    def     __delitem__( self, index ):
        
        try:
            del self.conditions[ index ]
        except IndexError:
            pass
    
    #//-------------------------------------------------------//
    
    def     SetValue( self, value, operation ):
        
        self.value = value
        self.operation = operation
    
    #//-------------------------------------------------------//
    
    def     GetValue( self ):
        return (self.operation, self.value )
    
    #//-------------------------------------------------------//
    
    def     IsTrue( self, options, op, current_value ):
        for c in self.conditions:
            if not c( options, op, current_value ):
                return 0
        
        return 1
    
    #//-------------------------------------------------------//
    
    def     Clone( self ):
        clone = _ConditionalValue()
        clone.conditions = self.conditions[:]
        clone.value = self.value
        clone.operation = self.operation
        
        return clone

#//===========================================================================//
#//===========================================================================//

class       _NoneOptions:
    
    def     __error( self ):    _Error("The option is not linked with any instance of options.")
    def     __setattr__(self, name, value):     self.__error()
    def     __setitem__( self, name, value ):   self.__error()
    def     __getattr__( self, name ):          self.__error()
    def     __getitem__(self, name ):           self.__error()
    def     OptionNames( self, opt ):           return [ None ]
    def     Cache( self ):                      return {}
    def     ClearCache( self ):                 pass

_none_options = _NoneOptions()

#//===========================================================================//
#//===========================================================================//

ccflags = vars.VarList( vars.VarString() )

vars.VarBool( name = 'ccflags'  )
vars.VarEnum( name = 'ccflags'  )
vars.VarList( name = 'ccflags'  )
vars.VarEnumList( name = 'ccflags'  )
vars.VarEnumUniqueList( name = 'ccflags' )


class  HelpText( object ):
  __slots__ = ( 'text', 'group' )
  
  def   __init__( self ):
    self.text = ''
    self.group = 'User'
  
  def   shortHelp( self, var ):
    return "Short descrition"
  
  def   help( self, var ):
    return "Detailed descrition"

#//-------------------------------------------------------//

class   Validator( object ):
    """
    Validates a converted simple value.
    """
    def   __call__( self, value )
        return True
    
    def   shortHelp( self, var ):
        return ""
    
    def   help( self, var ):
        return ""

#//-------------------------------------------------------//

class   Converter (object):
    """
    Converts a value into base value (string, int, bool, node)
    """
    def   __call__(self, value)
        return value

#//-------------------------------------------------------//

class   ConverterStr (object):
    """
    Converts a value into a string applying user's converter and validator
    """
    
    __slots__ = ( 'converter', 'validator' )
    
    def   __init__( self, comparator = None, converter = None, validator = None ):
        self.user_converter = user_converter
        self.user_validator = user_validator
        
    def   __call__(self, value)
        if value is not None:
            value = str(value)
         else:
             value = ''
        
        if self.user_converter is not None:
            value = self.user_converter( value )
        
        if self.user_validator is not None:
            value = self.user_converter( value )
        
        return value
        
    def   cmp(self, value1, value2 ):
        if 
    
    def   str(self, value):
        return self(value)

#//-------------------------------------------------------//

class   VarInt (OptionBase):
    
    def     __init__( self, **kw ):
        self.help = None
        self.
        
        
        kw['min'] = int( kw.get( 'min', -(sys.maxint - 1) ) )
        kw['max'] = int( kw.get( 'max', sys.maxint ) )
        
        if __debug__:
            if kw['min'] > kw['max']:
                _Error( "Minimal value: %d is greater than maximal value: %d " % (min, max) )
        
        kw['allowed_operations'] = ['+','-']
        
        self._init_base( **kw )
        self._set_default()
    
    #//-------------------------------------------------------//
    
    def     _convert_value( self, val ):
        
        try:
            int_val = int(str(val))
        
        except TypeError:
            _Error( "Invalid type of value: %s, type: %s" % (val, type(val)) )
        
        if (int_val < self.shared_data['min']) or (int_val > self.shared_data['max']):
            _Error( "The value: %s for option: '%s' is out of range: [%d..%d]" % \
                    (val, self.Name(), self.shared_data['min'], self.shared_data['max']) )
        
        return int_val
    
    #//-------------------------------------------------------//
    
    def     __int__( self ):
        return self.Value()
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        return '%d ... %d' % (self.shared_data['min'], self.shared_data['max'])
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List of integers in range: ' + self.AllowedValuesStr()
        
        return 'An integer in range: ' + self.AllowedValuesStr()


class   OptionBase:
    
    def     _init_base( self, **kw ):
        
        kw.setdefault( 'help', None )
        kw.setdefault( 'group', "User" )
        kw.setdefault( 'initial_value', None )
        kw.setdefault( 'unique', 1 )
        
        is_list = kw.setdefault( 'is_list', 0 )
        
        allowed_operations = kw.setdefault( 'allowed_operations', [] )
        
        if '=' not in allowed_operations:
            allowed_operations.append( '=' )
        
        if is_list:
            utils.appendToListUnique( allowed_operations, ['+', '-'] )
            kw.setdefault( 'separator', ' ' )
        else:
            kw.setdefault( 'separator', '' )
        
        if is_list:
            update = kw.setdefault( 'update', 'Append' )
        else:
            update = 'Set'
            kw['update'] = update
        
        self.Update = getattr( self, update )
        
        self.options = kw.get( 'options', _none_options )
        
        self.shared_data = kw
        
        self.conditions = []
    
    #//-------------------------------------------------------//
    
    def     _set_default( self ):
        
        initial_value = self.shared_data[ 'initial_value' ]
        
        if initial_value is None:
            return
        
        if '+' in self.shared_data[ 'allowed_operations' ]:
            self.Append( initial_value )
        else:
            self.Set( initial_value )
    
    #//-------------------------------------------------------//
    
    def     _clone( self, options ):
        clone = OptionBase()
        
        clone.__dict__ = self.__dict__.copy();
        clone.__class__ = self.__class__;
        
        clone.options = options
        clone.conditions = self.conditions[:]
        
        clone.Update = getattr( clone, clone.shared_data[ 'update' ] )
        
        return clone
    
    #//-------------------------------------------------------//
    
    def     SetOptions( self, options ):
        
        if not _is_options( self.options ):
            self.options = options
       
        elif self.options is not options:
            _Error("The option is already linked with another options.")
    
    #//-------------------------------------------------------//
    
    def     Name( self ):
        return self.options.OptionNames( self )[0]
    
    #//-------------------------------------------------------//
    
    def     __value( self ):
        
        value = None
        
        options = self.options
        
        for c in self.conditions:
            if c.IsTrue( options, self, value ):
                
                op, v = c.GetValue()
                v = v.Get( self, value )
                
                if op == '=':
                    value = v
                
                elif v is None:
                    continue
                
                elif op == '+':
                    if value is None:
                        value = v
                    else:
                        value += v
                
                elif op == '-':
                    if value is not None:
                        value -= v
        
        return value
    
    #//-------------------------------------------------------//
    
    def     __value_list( self,
                     appendToList = utils.appendToListUnique,
                     removeFromList = utils.removeFromList ):
        
        values = []
        
        if not self.shared_data['unique']:
            def     appendListToList( values_list, values ):
                values_list += values
            appendToList = appendListToList
        
        options = self.options
        
        for c in self.conditions:
            if c.IsTrue( options, self, values ):
                
                op, v = c.GetValue()
                v = v.Get( self, values )
                
                if op == '=':
                    values = v
                
                elif op == '+':
                    appendToList( values, v )
                
                elif op == '-':
                    removeFromList( values, v )
        
        return values
    
    #//-------------------------------------------------------//
    
    def     Value( self, id = id ):
        
        cache = self.options.Cache()
        id_self = id(self)
        
        try:
            return cache[ id_self ]
        except KeyError:
            pass
        
        if self.shared_data['is_list']:
            value = self.__value_list()
        else:
            value = self.__value()
        
        cache[ id_self ] = value
        
        return value
    
    #//-------------------------------------------------------//
    
    def     Set( self, value ):
        self.SetIf( _always_true_condition, value )
    
    #//-------------------------------------------------------//
    
    def     Preset( self, value ):
        self.PresetIf( _always_true_condition, value )
    
    #//-------------------------------------------------------//
    
    def     Append( self, value ):
        self.AppendIf( _always_true_condition, value )
    
    #//-------------------------------------------------------//
    
    def     Prepend( self, value ):
        self.PrependIf( _always_true_condition, value )
    
    #//-------------------------------------------------------//
    
    def     Remove( self, value ):
        self.RemoveIf( _always_true_condition, value )
    
    #//-------------------------------------------------------//
    
    def     __iadd__(self, value ):
        self.Append( value )
        return self
    
    #//-------------------------------------------------------//
    
    def     __isub__(self, value ):
        self.Remove( value )
        return self
    
    #//-------------------------------------------------------//
    
    def     SetIf( self, condition, value ):
        self._add_condition( condition, value, '=')
    
    #//-------------------------------------------------------//
    
    def     PresetIf( self, condition, value ):
        self._add_condition( condition, value, '=', pre = 1)
    
    #//-------------------------------------------------------//
    
    def     AppendIf( self, condition, value ):
        self._add_condition( condition, value, '+')
    
    #//-------------------------------------------------------//
    
    def     PrependIf( self, condition, value ):
        self._add_condition( condition, value, '+', pre = 1)
    
    #//-------------------------------------------------------//
    
    def     RemoveIf( self, condition, value ):
        self._add_condition( condition, value, '-' )
    
    #//-------------------------------------------------------//
    
    def     _add_condition( self, condition, value, operation, pre = 0 ):
        
        if __debug__:
            if operation not in self.shared_data['allowed_operations']:
                _Error( "Operation: '%s' is not allowed for option: '%s'" % (operation, self.Name()) )
        
        value = _MakeValue( value, self )
        
        conditional_value = _ConditionalValue()
        conditional_value.Append( condition )
        
        conditional_value.SetValue( value, operation )
        
        if not pre:
            if (operation == '=') and (condition is _always_true_condition):
                
                # clear the conditions list if it's an unconditional set
                self.conditions = []
            
            self.conditions.append( conditional_value )
        else:
            self.conditions.insert( 0, conditional_value )
        
        self.options.ClearCache()
    
    #//-------------------------------------------------------//
    
    def     Convert( self, value ):
        if value is self:
            return self.Value()
        
        return _MakeValue( value, self ).Get( self, None )
    
    def     __lt__( self, other):       return _lt( self, self.Value(), _MakeValue( other, self ) )
    def     __le__( self, other):       return _le( self, self.Value(), _MakeValue( other, self ) )
    def     __eq__( self, other):       return _eq( self, self.Value(), _MakeValue( other, self ) )
    def     __ne__( self, other):       return _ne( self, self.Value(), _MakeValue( other, self ) )
    def     __gt__( self, other):       return _gt( self, self.Value(), _MakeValue( other, self ) )
    def     __ge__( self, other):       return _ge( self, self.Value(), _MakeValue( other, self ) )
    
    def     __contains__(self, other):  return self.has( other )
    def     has( self, other ):         return _has( self, self.Value(), _ValueList( other, self ) )
    def     has_any( self, other ):     return _has_any( self, self.Value(), _ValueList( other, self ) )
    def     one_of( self, values ):     return _one_of( self, self.Value(), _ValueList( values, self ) )
    
    #//-------------------------------------------------------//
    
    def     __nonzero__( self ):
        if self.Value(): return 1
        return 0
    
    #//-------------------------------------------------------//
    
    def     __str__( self, map = map, str = str ):
        
        if self.shared_data['is_list']:
            return self.shared_data['separator'].join( map(str, self.Value() ) )
        
        value = self.Value()
        if value is None:
            return ''
        
        return str( value )


#//===========================================================================//
#//===========================================================================//

class   BoolOption (OptionBase):
    
    __invert_true = {
               'y': 'no',
               'yes': 'no',
               't': 'false',
               '1': 'false',
               'true': 'false',
               'on': 'off',
               'enabled' : 'disabled' }
               
    __invert_false = {
               'n': 'yes',
               'no': 'yes',
               'f': 'true',
               '0': 'true',
               'false': 'true',
               'off': 'on',
               'disabled' : 'enabled',
               'none' : 'true'
             }
    
    __invert_bool = __invert_true.copy()
    __invert_bool.update( __invert_false )
    
    #//-------------------------------------------------------//
    def     __init__( self, **kw ):
        
        self._init_base( **kw )
        self._set_default()
    
    #//-------------------------------------------------------//
    
    def     _convert_value( self, val,
                            str = str,
                            invert_true = __invert_true,
                            invert_false = __invert_false ):
        
        lval = str( val ).lower()
        if invert_true.has_key( lval ):     return 1
        if invert_false.has_key( lval ):    return 0
        
        _Error( "Invalid boolean value: '%s'" % (val) )
    
    #//-------------------------------------------------------//
    
    def     __str__( self ):
        
        initial_value = self.shared_data['initial_value']
        
        value_str = self.__invert_bool[ str( initial_value ).lower() ]
        
        if self == initial_value:
            value_str = self.__invert_bool[ value_str ]
        
        return value_str
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        return 'yes/no, true/false, on/off, enabled/disabled, 1/0'
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List of boolean values: ' + self.AllowedValuesStr()
        
        return 'A boolean value: ' + self.AllowedValuesStr()
    

#//===========================================================================//
#//===========================================================================//

class   EnumOption (OptionBase):
    
    def     __init__( self, **kw ):
        
        kw['values_dict'] = {}
        kw.setdefault('all_key', 'all')
        
        aliases = kw.get( 'aliases', {} )
        allowed_values = kw.get( 'allowed_values', () )
        
        self._init_base( **kw )
        
        self.AddValues( allowed_values )
        self.AddAliases( aliases )
        
        self._set_default()
        
    #//-------------------------------------------------------//
    
    def     __map_values( self, values, toSequence = utils.toSequence ):
        
        values_dict = self.shared_data['values_dict']
        
        mapped_values = []
        
        for v in toSequence( values ):
            
            try:
                v = str(v).lower()
                alias = values_dict[ v ]
            
            except (AttributeError, KeyError):
                
                if self.shared_data['all_key'] == v:
                    alias = self.AllowedValues()
                
                else:
                    return None
            
            if alias is None:
                mapped_values.append( v )
            else:
                mapped_values += alias
        
        return mapped_values
    
    #//=======================================================//
    
    def     _convert_value( self, val ):
        
        values = self.__map_values( val )
        
        if not values:
            _Error( "Invalid value: '%s', type: %s" % (val, type(val)) )
        
        if len( values ) == 1:
            return values[0]
        
        return values
    
    #//=======================================================//
    
    def     AddValues( self, values, toSequence = utils.toSequence ):
        values_dict = self.shared_data['values_dict']
        
        for v in toSequence( values ):
            
            try:
                v = v.lower()
            except AttributeError:
                _Error( "Invalid value: '%s', type: %s" % (val, type(val)) )
            
            if self.__map_values( v ):
                _Error( "Can't change an existing value: %s" % (v) )
            
            values_dict[ v ] = None
    
    #//=======================================================//
    
    def     AddAlias( self, alias, values, isSequence = utils.isSequence ):
        
        if self.__map_values( alias ):
            _Error( "Can't change an existing value: %s" % (alias) )
        
        mapped_values = self.__map_values( values )
        if not mapped_values:
            _Error( "Invalid value(s): %s" % (values) )
        
        if (not self.shared_data['is_list']) and (len( mapped_values ) > 1):
            _Error( "Can't add an alias to list of values: %s of none-list option" % (mapped_values) )
        
        self.shared_data['values_dict'][ alias ] = mapped_values
    
    #//=======================================================//
    
    def     AddAliases( self, aliases,
                        isDict = utils.isDict ):
        
        if not aliases:
            return
        
        if __debug__:
            if not isDict( aliases ):
                _Error( "Aliases must be a dictionary" )
        
        for a,v in aliases.iteritems():
            self.AddAlias( a, v )
    
    #//=======================================================//
    
    def     AllowedValues( self ):
        
        allowed_values = []
        
        for a,v in self.shared_data['values_dict'].iteritems():
            if v is None:
                allowed_values.append( a )
        
        return allowed_values
    
    #//=======================================================//
    
    def     Aliases( self ):
        
        aliases = {}
        
        for a,v in self.shared_data['values_dict'].iteritems():
            
            if v is not None:
                if len(v) == 1:
                    tmp = aliases.get( v[0] )
                    if tmp:
                        aliases[ v[0] ] = tmp + [ a ]
                    else:
                        aliases[ v[0] ] = [ a ]
            else:
                aliases.setdefault( a )
        
        return aliases
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        
        allowed_values = []
        
        aliases = self.Aliases()
        values = aliases.keys()
        values.sort()
        
        for v in values:
            
            a = aliases[v]
            
            if a is not None:
                a.sort()
                v = v + ' (or ' + ", ".join( a ) + ')'
            
            allowed_values.append( v )
        
        allowed_values = map( lambda v: '- ' + v, allowed_values )
        allowed_values_str = '\n'.join( allowed_values )
        
        if len(allowed_values) > 1:
            allowed_values_str = '\n' + allowed_values_str
        
        return allowed_values_str
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List of values: ' + self.AllowedValuesStr()
        
        return 'A value: ' + self.AllowedValuesStr()
    


#//===========================================================================//
#//===========================================================================//

class   IntOption (OptionBase):
    
    def     __init__( self, **kw ):
        
        kw['min'] = int( kw.get( 'min', -(sys.maxint - 1) ) )
        kw['max'] = int( kw.get( 'max', sys.maxint ) )
        
        if __debug__:
            if kw['min'] > kw['max']:
                _Error( "Minimal value: %d is greater than maximal value: %d " % (min, max) )
        
        kw['allowed_operations'] = ['+','-']
        
        self._init_base( **kw )
        self._set_default()
    
    #//-------------------------------------------------------//
    
    def     _convert_value( self, val ):
        
        try:
            int_val = int(val)
        
        except TypeError:
            _Error( "Invalid type of value: %s, type: %s" % (val, type(val)) )
        
        if (int_val < self.shared_data['min']) or (int_val > self.shared_data['max']):
            _Error( "The value: %s for option: '%s' is out of range: [%d..%d]" % \
                    (val, self.Name(), self.shared_data['min'], self.shared_data['max']) )
        
        return int_val
    
    #//-------------------------------------------------------//
    
    def     __int__( self ):
        return self.Value()
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        return '%d ... %d' % (self.shared_data['min'], self.shared_data['max'])
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List of integers in range: ' + self.AllowedValuesStr()
        
        return 'An integer in range: ' + self.AllowedValuesStr()


#//===========================================================================//
#//===========================================================================//

class   StrOption (OptionBase):
    
    def     __init__( self, **kw ):
        
        kw.setdefault( 'ignore_case', 0 )
        
        kw['allowed_operations'] = ['+']
        
        self._init_base( **kw )
        self._set_default()
    
    #//-------------------------------------------------------//
    
    def     _convert_value( self, value ):
        
        if value is None:
            return ''
        
        value = str(value)
        if self.shared_data['ignore_case']:
            value = value.lower()
        
        return value
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        return 'string'

    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List of strings'
        
        return 'A string'


#//===========================================================================//
#//===========================================================================//

class   LinkedOption (OptionBase):
    
    def     __init__( self, **kw ):
        
        if not kw.get( 'linked_opt_name' ):
            _Error('Linked option name has not been passed. linked_opt_name is not set. ')
        
        self._init_base( **kw )
        self._set_default()
    
    #//-------------------------------------------------------//
    
    def     _convert_value( self, value, isSequence = utils.isSequence ):
        
        linked_option = self.options[ self.shared_data['linked_opt_name'] ]
        
        value = linked_option._convert_value( value )
        
        if isSequence( value ) and (len( value ) == 1):
            return value[0]
        
        return value
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        linked_option = self.options[ self.shared_data['linked_opt_name'] ]
        return linked_option.AllowedValuesStr()
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List of values: ' + self.AllowedValuesStr()
        
        return 'A value: ' + self.AllowedValuesStr()


#//===========================================================================//
#//===========================================================================//

class   VersionOption (OptionBase):
    
    def     __init__( self, **kw ):
        
        self._init_base( **kw )
        self._set_default()
    
    #//-------------------------------------------------------//
    
    def     _convert_value( self, val, _Version = version.Version ):
        return _Version( val )
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        return 'Version in format N[a].N[a].N[a]... (where N - dec numbers, a - alphas)'
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List: ' + self.AllowedValuesStr()
        
        return self.AllowedValuesStr()

#//===========================================================================//
#//===========================================================================//

class   PathOption (OptionBase):
    
    def     __init__( self, **kw ):
        
        kw.setdefault( 'separator', os.pathsep )
        kw.setdefault( 'is_node', 0 )
        
        self._init_base( **kw )
        self._set_default()
    
    #//-------------------------------------------------------//
    
    def     _convert_value( self, val,
                            hasattr = hasattr,
                            normcase = os.path.normcase,
                            abspath = os.path.abspath ):
        
        if (hasattr( val, 'env' ) and hasattr( val, 'labspath' ) and hasattr( val, 'path_elements' )):
            # it is likely that this is a Node object, just return it as it is
            return val
        
        if val is None:
            _Error( "Invalid value: %s, type: %s" % (val, type(val)) )
        
        if self.shared_data['is_node']:
            env = self.options.Env()
            
            if env is not None:
                return env.Dir( str(val) ).srcnode()
        
        return normcase( abspath( str(val) ) )
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesStr( self ):
        return 'A file system path'
    
    #//-------------------------------------------------------//
    
    def     AllowedValuesHelp( self ):
        if self.shared_data['is_list']:
            return 'List of file system paths'
        
        return 'A file system path'

#//===========================================================================//
#//===========================================================================//

class _ConditionalOptions:
    
    def     __init__( self, options, conditional_value = None ):
        
        self.__dict__['__options'] = options
        
        if conditional_value is not None:
            self.__dict__['__conditional_value'] = conditional_value.Clone()
        else:
            self.__dict__['__conditional_value'] = _ConditionalValue()
    
    #//-------------------------------------------------------//
    
    def     __setattr__(self, name, value):
        
        options = self.__dict__['__options']
        option = options.get( name )
        
        if option is None:
            if _is_option( value ):
                _Error( "Can't add new option '%s' within condition." % (name) )
            else:
                _Error( "Unknown option: %s" % (name) )
        
        if option is value:
            return
        
        option.SetIf( self.__dict__['__conditional_value'], value )
    
    #//-------------------------------------------------------//
    
    def     __setitem__( self, name, value ):
        self.__setattr__( name, value )
    
    #//-------------------------------------------------------//
    
    def     __getattr__( self, name ):
        
        options = self.__dict__['__options']
        option = options.get( name )
        
        if option is None:
            _Error( "Unknown option: %s" % (name) )
        
        return _ConditionalOption( name, option, options, self.__dict__['__conditional_value'] )
    
    #//-------------------------------------------------------//
    
    def     __getitem__(self, name ):
        return self.__getattr__( name )
    
    #//-------------------------------------------------------//
    
    def     __repr__( self ):
        return "<_Conditional Options>"

#//===========================================================================//
#//===========================================================================//

class   _ConditionalOption:
    
    def     __init__( self, name, option, options, conditional_value ):
        
        self.name = name
        self.option = option
        self.options = options
        self.conditional_value = conditional_value
    
    #//-------------------------------------------------------//
    
    def     __add_condition( self, value, operation, condition = None, pre = 0 ):
        
        conditional_value = self.conditional_value
        
        if condition is not None:
            conditional_value = conditional_value.Clone()
            conditional_value.Append( condition )
        
        self.option._add_condition( conditional_value, value, operation, pre )
    
    #//-------------------------------------------------------//
    
    def     Set( self, value ):                     self.__add_condition( value, '=' )
    def     Preset( self, value ):                  self.__add_condition( value, '=', pre = 1 )
    def     SetIf( self, condition, value ):        self.__add_condition( value, '=', condition )
    def     PresetIf( self, condition, value ):     self.__add_condition( value, '=', condition, pre = 1 )
    def     Append( self, value ):                  self.__add_condition( value, '+' )
    def     Prepend( self, value ):                 self.__add_condition( value, '+', pre = 1 )
    def     AppendIf( self, condition, value ):     self.__add_condition( value, '+', condition )
    def     PrependIf( self, condition, value ):    self.__add_condition( value, '+', condition, pre = 1 )
    def     Remove( self, value ):                  self.__add_condition( value, '-' )
    def     RemoveIf( self, condition, value ):     self.__add_condition( value, '-', condition )
    
    #//-------------------------------------------------------//
    
    def     __iadd__( self, value ):
        self.Append( value )
        return self.option
    
    #//-------------------------------------------------------//
    
    def     __isub__( self, value ):
        self.Remove( value )
        return self.option
    
    #//-------------------------------------------------------//
    
    def     __getitem__( self, value ):
        
        if self.option.shared_data['is_list']:
            return self.has( value )
        
        return self.eq( value )
    
    #//-------------------------------------------------------//
    
    def     __cond_options( self, cond_function, value ):
        
        conditional_value = self.conditional_value.Clone()
        
        value = _MakeValue( value, self.option )
        conditional_value.Append( _Condition( self.name, cond_function, value ) )
        
        return _ConditionalOptions( self.options, conditional_value )
    
    #//-------------------------------------------------------//
    
    def     has( self, value ):         return self.__cond_options( _has, _ValueList( value, self.option ) )
    def     has_any( self, values ):    return self.__cond_options( _has_any, _ValueList( values, self.option ) )
    def     one_of( self, values ):     return self.__cond_options( _one_of, _ValueList( values, self.option ) )
    def     eq( self, value ):          return self.__cond_options( _eq, value )
    def     ne( self, value ):          return self.__cond_options( _ne, value )
    def     gt( self, value ):          return self.__cond_options( _gt, value )
    def     ge( self, value ):          return self.__cond_options( _ge, value )
    def     lt( self, value ):          return self.__cond_options( _lt, value )
    def     le( self, value ):          return self.__cond_options( _le, value )
