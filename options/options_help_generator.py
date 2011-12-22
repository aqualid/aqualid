
def     _print_option_help( op, names, detailed_help, prefix, help_justification ):
    
    help = ''
    
    if detailed_help:
        for name in names[:-1]:
            help += prefix + name + ':\n'
    
    name = names[-1]
    
    tmp = prefix + name + ':'
    help += tmp
    help += ' ' * (len( help_justification ) - len(tmp))
    
    h = op.shared_data['help']
    
    if detailed_help:
        help += h.replace('\n', '\n' + help_justification )
        
        if help[-1] != '\n':    help += '\n'
        
        val_help = help_justification + 'Type: '
        help += val_help
        
        val_just = ' ' * len(val_help)
        val_help = op.AllowedValuesHelp()
        
        val_help = val_help.replace('\n', '\n' + val_just )
        
        help += val_help + '\n'
    
    else:
        line_end = h.find('\n')
        if line_end == -1:
            help += h
        else:
            help += h[:line_end]
        
        help += '\n'
    
    return help

#//---------------------------------------------------------------------------//

def     GenerateOptionsHelp( options, detailed_help ):
    
    prefix = "  "
    
    help = "\nOptions to control builds.\n" \
           "The values can be overridden via a command line.\n" \
           "Like this: scons optimization=speed debug_info=1 cc_name=gcc\n" \
           "Or within your build scripts or config files.\n"
    help += '=' * max( map(len, help.split('\n')) ) + '\n'
    
    sorted_options = []
    
    max_name_len = 0
    
    for op, names   in  options.__dict__['__ids_dict'].itervalues():
        
        if op.shared_data['help'] is None:
            continue
        
        names = list(names)
        names.sort( lambda a,b: cmp( len(a), len(b)) or cmp( a, b ) )
        
        max_name_len = max( [ max_name_len, len( names[-1] ) ] )
        
        sorted_options.append( (op, names) )
    
    help_justification = ' ' * (max_name_len + len(prefix) + 1 + 2)
    
    def     _cmp_options( op_names1, op_names2 ):
        
        op1,names1 = op_names1
        op2,names2 = op_names2
        
        g1 = op1.shared_data['group']
        g2 = op2.shared_data['group']
        
        if g1 == 'User' and g2 != 'User':
            return 1
        
        if g1 != 'User' and g2 == 'User':
            return -1
        
        result = cmp( g1, g2 )
        if result == 0:
            result = cmp( names1[-1].lower(), names2[-1].lower() )
        
        return result
    
    sorted_options.sort( _cmp_options )
    
    group = ''
    
    for n in sorted_options:
        
        op    = n[0]
        names = n[1]
        
        g = op.shared_data['group']
        if g != group:
            group = g
            if help[-1] != '\n': help += '\n'
            help += '\n*** ' + group + ' options ***:\n\n'
        
        else:
            if help[-1] != '\n': help += '\n'
        
        op_help = _print_option_help( op, names, detailed_help, prefix, help_justification )
        
        if op_help.count('\n') > 1:
            if not help.endswith( '\n\n' ):
                help += '\n'
            
            help += op_help + '\n'
        else:
            help += op_help
    
    help += '\n'
    
    return help
