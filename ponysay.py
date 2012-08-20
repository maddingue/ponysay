#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
ponysay.py - Ponysay, a cowsay wrapper for ponies
Copyright (C) 2012  Erkin Batu Altunbaş

Authors: Erkin Batu Altunbaş:              Project leader, helped write the first implementation
         Mattias "maandree" Andrée:        Major contributor of both implementions
         Elis "etu" Axelsson:              Major contributor of current implemention and patcher of the first implementation
         Sven-Hendrik "svenstaro" Haase:   Major contributor of the first implementation
         Jan Alexander "heftig" Steffens:  Major contributor of the first implementation
         Kyah "L-four" Rindlisbacher:      Patched the first implementation

License: WTFPL
'''

import os
import sys
import random
from subprocess import Popen, PIPE


'''
The version of ponysay
'''
VERSION = '2.1'


'''
The directory where ponysay is installed, this is modified when building with make
'''
INSTALLDIR = '/usr'


'''
The user's home directory
'''
HOME = os.environ['HOME']


'''
Whether the program is execute in Linux VT (TTY)
'''
linuxvt = os.environ['TERM'] == 'linux'


'''
Whether the script is executed as ponythink
'''
isthink = (len(__file__) >= 8) and (__file__[-8:] == 'think.py')


'''
Whether stdin is piped
'''
pipelinein = not sys.stdin.isatty()

'''
Whether stdout is piped
'''
pipelineout = False #not sys.stdout.isatty()  # currently impossible, we need to get rid of the little shell script first

'''
Whether stderr is piped
'''
pipelineerr = not sys.stderr.isatty()


'''
The directories where pony files are stored, ttyponies/ are used if the terminal is Linux VT (also known as TTY)
'''
ponydirs = []
if linuxvt:  _ponydirs = [HOME + '/.local/share/ponysay/ttyponies/',  INSTALLDIR + '/share/ponysay/ttyponies/']
else:        _ponydirs = [HOME + '/.local/share/ponysay/ponies/',     INSTALLDIR + '/share/ponysay/ponies/'   ]
for ponydir in _ponydirs:
    if os.path.isdir(ponydir):
        ponydirs.append(ponydir)


'''
The directories where quotes files are stored
'''
quotedirs = []
_quotedirs = [HOME + '/.local/share/ponysay/quotes/',  INSTALLDIR + '/share/ponysay/quotes/']
for quotedir in _quotedirs:
    if os.path.isdir(quotedir):
        quotedirs.append(quotedir)



'''
This is the mane class of ponysay
'''
class Ponysay():
    '''
    Starts the part of the program the arguments indicate
    '''
    def __init__(self, args):
        if (args.argcount == 0) and not pipelinein:
            args.help()
            return
        
        if (args.opts['-l'] is not None) and pipelineout:
            args.opts['--onelist'] = args.opts['-l']
            args.opts['-l'] = None
        
        if   args.opts['-h']        is not None:  args.help()
        elif args.opts['--quoters'] is not None:  self.quoters()
        elif args.opts['--onelist'] is not None:  self.onelist()
        elif args.opts['-v']        is not None:  self.version()
        elif args.opts['-l']        is not None:  self.list()
        elif args.opts['-L']        is not None:  self.linklist()
        elif args.opts['-q']        is not None:  self.quote(args)
        else:                                     self.print_pony(args)
    
    
    ##
    ## Auxiliary methods
    ##
    
    '''
    Returns one file with full path, names is filter for names, also accepts filepaths.
    '''
    def __getponypath(self, names = None):
        ponies = {}
        
        if not names == None:
            for name in names:
                if os.path.isfile(name):
                    ponies[name] = name
        
        for ponydir in ponydirs:
            for ponyfile in os.listdir(ponydir):
                pony = ponyfile[:-5]
                if pony not in ponies:
                    ponies[pony] = ponydir + ponyfile
        
        if names == None:
            names = list(ponies.keys())
        
        pony = names[random.randrange(0, len(names))]
        if pony not in ponies:
            sys.stderr.write('I have never heared of any pony named %s\n' % (pony));
            exit(1)
        else:
            return ponies[pony]
    
    
    '''
    Returns a set with all ponies that have quotes and are displayable
    '''
    def __quoters(self):
        quotes = []
        quoteshash = set()
        _quotes = []
        for quotedir in quotedirs:
            _quotes += [item[:item.index('.')] for item in os.listdir(INSTALLDIR + '/share/ponysay/quotes/')]
        for quote in _quotes:
            if not quote == '':
                if not quote in quoteshash:
                    quoteshash.add(quote)
                    quotes.append(quote)
        
        ponies = set()
        for ponydir in ponydirs:
            for pony in os.listdir(ponydir):
                if not pony[0] == '.':
                    p = pony[:-5] # remove .pony
                    for quote in quotes:
                        if ('+' + p + '+') in ('+' + quote + '+'):
                            if not p in ponies:
                                ponies.add(p)
        
        return ponies
    
    
    '''
    Returns a list with all (pony, quote file) pairs
    '''
    def __quotes(self):
        quotes = []
        for quotedir in quotedirs:
            quotes += [quotedir + item for item in os.listdir(quotedir)]
        rc = []
        
        for ponydir in ponydirs:
            for pony in os.listdir(ponydir):
                if not pony[0] == '.':
                    p = pony[:-5] # remove .pony
                    for quote in quotes:
                        q = quote[quote.rindex('/') + 1:]
                        q = q[:q.rindex('.')]
                        if ('+' + p + '+') in ('+' + q + '+'):
                            rc.append((p, quote))
        
        return rc
    
    
    '''
    Gets the size of the terminal in (rows, columns)
    '''
    def __gettermsize(self):
        termsize = Popen(['stty', 'size'], stdout=PIPE, stdin=sys.stderr).communicate()[0]
        termsize = termsize.decode('utf8', 'replace')[:-1].split(' ') # [:-1] removes a \n
        termsize = [int(item) for item in termsize]
        return termsize
    
    
    ##
    ## Listing methods
    ##
    
    '''
    Lists the available ponies
    '''
    def list(self):
        termsize = self.__gettermsize()
        quoters = self.__quoters()
        
        for ponydir in ponydirs: # Loop ponydirs
            print('\033[1mponyfiles located in ' + ponydir + '\033[21m')
            
            ponies = os.listdir(ponydir)
            ponies = [item[:-5] for item in ponies] # remove .pony from file name
            ponies.sort()
            
            width = len(max(ponies, key = len)) + 2 # Get the longest ponyfilename lenght + 2 spaces
            
            x = 0
            for pony in ponies:
                spacing = ' ' * (width - len(pony))
                print(('\033[1m' + pony + '\033[21m' if (pony in quoters) else pony) + spacing, end='') # Print ponyfilename
                x += width
                if x > (termsize[1] - width): # If too wide, make new line
                    print()
                    x = 0
                    
            print('\n');
    
    
    '''
    Lists the available ponies with alternatives inside brackets
    '''
    def linklist(self):
        termsize = self.__gettermsize()
        quoters = self.__quoters()
        
        for ponydir in ponydirs: # Loop ponydirs
            print('\033[1mponyfiles located in ' + ponydir + '\033[21m')
            
            files = os.listdir(ponydir)
            files = [item[:-5] for item in files] # remove .pony from file name
            files.sort()
            pairs = [(item, os.readlink(ponydir + item + '.pony') if os.path.islink(ponydir + item + '.pony') else '') for item in files]
            
            ponymap = {}
            for pair in pairs:
                if pair[1] == '':
                    if pair[0] not in ponymap:
                        ponymap[pair[0]] = []
                else:
                    target = pair[1][:-5]
                    if '/' in target:
                        target = target[target.rindex('/') + 1:]
                    if target in ponymap:
                        ponymap[target].append(pair[0])
                    else:
                        ponymap[target] = [pair[0]]
            
            width = 0
            ponies = []
            widths = []
            for pony in ponymap:
                w = len(pony)
                item = '\033[1m' + pony + '\033[21m' if (pony in quoters) else pony
                syms = ponymap[pony]
                if len(syms) > 0:
                    w += 2 + len(syms)
                    item += ' ('
                    first = True
                    for sym in syms:
                        w += len(sym)
                        if not first:
                            item += ' '
                        else:
                            first = False
                        item += '\033[1m' + sym + '\033[21m' if (sym in quoters) else sym
                    item += ')'
                ponies.append(item)
                widths.append(w)
                if width < w:
                    width = w
            
            width += 2;
            x = 0
            index = 0
            for pony in ponies:
                spacing = ' ' * (width - widths[index])
                index += 1
                print(pony + spacing, end='') # Print ponyfilename
                x += width
                if x > (termsize[1] - width): # If too wide, make new line
                    print()
                    x = 0
            
            print('\n');
    
    
    '''
    Lists with all ponies that have quotes and are displayable
    '''
    def quoters(self):
        last = ''
        ponies = []
        for pony in self.__quoters():
            ponies.append(pony)
        ponies.sort()
        for pony in ponies:
            if not pony == last:
                last = pony
                print(pony)
    
    
    '''
    Lists the available ponies one one column without anything bold
    '''
    def onelist(self):
        last = ''
        ponies = []
        for ponydir in ponydirs: # Loop ponydirs
            ponies += os.listdir(ponydir)
        ponies = [item[:-5] for item in ponies] # remove .pony from file name
        ponies.sort()
        for pony in ponies:
            if not pony == last:
                last = pony
                print(pony)
    
    
    ##
    ## Displaying methods
    ##
    
    '''
    Prints the name of the program and the version of the program
    '''
    def version(self):
        print('%s %s' % ('ponysay', VERSION))
    
    
    '''
    Returns (the cowsay command, whether it is a custom program)
    '''
    def __getcowsay(self):
        if isthink:
            cowthink = os.environ['PONYSAY_COWTHINK'] if 'PONYSAY_COWTHINK' in os.environ else None
            return ('cowthink', False) if (cowthink is None) or (cowthink == '') else (cowthink, True)
        
        cowsay = os.environ['PONYSAY_COWSAY'] if 'PONYSAY_COWSAY' in os.environ else None
        return ('cowsay', False) if (cowsay is None) or (cowsay == '') else (cowsay, True)
    
    
    '''
    Print the pony with a speech or though bubble. message, pony and wrap from args are used.
    '''
    def print_pony(self, args):
        if args.message == None:
            msg = ''.join(sys.stdin.readlines()).rstrip()
        else:
            msg = args.message
        
        
        pony = self.__getponypath(args.opts['-f'])
        (cowsay, customcowsay) = self.__getcowsay()
        
        if (len(pony) > 4) and (pony[-4:].lower() == '.png'):
            pony = '\'' + pony.replace('\'', '\'\\\'\'') + '\''
            pngcmd = ('img2ponysay -p -- ' if linuxvt else 'img2ponysay -- ') + pony
            pngpipe = os.pipe()
            Popen(pngcmd, stdout=os.fdopen(pngpipe[1], 'w'), shell=True).wait()
            pony = '/proc/' + str(os.getpid()) + '/fd/' + str(pngpipe[0])
        
        cmd = [cowsay, '-f', self.__kms(pony)]
        if args.opts['-W'] is not None:
            cmd += ['-W', args.opts['-W'][0]]
        cmd.append(msg)
        
        if linuxvt:
            print('\033[H\033[2J', end='')
        
        env_width = os.environ['PONYSAY_FULL_WIDTH'] if 'PONYSAY_FULL_WIDTH' in os.environ else None
        if env_width is None:  env_width = ''
        widthtruncation = self.__gettermsize()[1] if env_width not in ('yes', 'y', '1') else None
        messagewrap = int(args.opts['-W'][0]) if args.opts['-W'] is not None else None
        
        proc = Backend(message = msg, ponyfile = pony, wrapcolumn = messagewrap if messagewrap is not None else 40, width = widthtruncation) # Popen(cmd, stdout=PIPE, stdin=sys.stderr)
        exit_value = 0
        #try:
        proc.parse()
        #except:
        #    exit_value = 1
        output = proc.output # proc.communicate()[0].decode('utf8', 'replace')
        if (len(output) > 0) and (output[-1] == '\n'):
            output = output[:-1]
        
        
        env_bottom = os.environ['PONYSAY_BOTTOM'] if 'PONYSAY_BOTTOM' in os.environ else None
        if env_bottom is None:  env_bottom = ''
        
        env_height = os.environ['PONYSAY_TRUNCATE_HEIGHT'] if 'PONYSAY_TRUNCATE_HEIGHT' in os.environ else None
        if env_height is None:  env_height = ''
        
        env_lines = os.environ['PONYSAY_SHELL_LINES'] if 'PONYSAY_SHELL_LINES' in os.environ else None
        if (env_lines is None) or (env_lines == ''):  env_lines = '2'
        
        lines = self.__gettermsize()[0] - int(env_lines)
        
        
        if not exit_value == 0:
            sys.stderr.write('Unable to successfully execute' + (' custom ' if customcowsay else ' ') + 'cowsay [' + cowsay + ']\n')
        else:
            if linuxvt or (env_height is ('yes', 'y', '1')):
                if env_bottom is ('yes', 'y', '1'):
                    for line in output[: -lines]:
                        print(line)
                else:
                    for line in output[: lines]:
                        print(line)
            else:
                print(output);
    
    
    '''
    Print the pony with a speech or though bubble and a self quote
    '''
    def quote(self, args):
        pairs = self.__quotes()
        if len(args.opts['-q']) > 0:
            ponyset = set(args.opts['-q'])
            alts = []
            for pair in pairs:
                if pair[0] in ponyset:
                    alts.append(pair)
            pairs = alts
            
        if not len(pairs) == 0:
            pair = pairs[random.randrange(0, len(pairs))]
            qfile = None
            try:
                qfile = open(pair[1], 'r')
                args.message = '\n'.join(qfile.readlines()).strip()
            finally:
                if qfile is not None:
                    qfile.close()
            args.opts['-f'] = [pair[0]]
        elif len(args.opts['-q']) == 0:
            sys.stderr.write('All the ponies are mute! Call the Princess!\n')
            exit(1)
        else:
            args.opts['-f'] = [args.opts['-q'][random.randrange(0, len(args.opts['-q']))]]
            args.message = 'I got nuthin\' good to say :('
        
        self.print_pony(args)
    
    
    '''
    Returns the file name of the input pony converted to a KMS pony, or if KMS is not used, the input pony itself
    '''
    def __kms(self, pony):
        if not linuxvt:
            return pony
        
        env_kms = os.environ['PONYSAY_KMS_PALETTE'] if 'PONYSAY_KMS_PALETTE' in os.environ else None
        if env_kms is None:  env_kms = ''
        
        env_kms_cmd = os.environ['PONYSAY_KMS_PALETTE_CMD'] if 'PONYSAY_KMS_PALETTE_CMD' in os.environ else None
        if (env_kms_cmd is not None) and (not env_kms_cmd == ''):
            env_kms = Popen(shlex.split(env_kms_cmd), stdout=PIPE, stdin=sys.stderr).communicate()[0].decode('utf8', 'replace')
            if env_kms[-1] == '\n':
                env_kms = env_kms[:-1]
        
        if env_kms == '':
            return pony
        
        palette = env_kms
        palettefile = env_kms.replace('\033]P', '')
        
        kmsponies = '/var/cache/ponysay/kmsponies/' + palettefile
        kmspony = (kmsponies + pony).replace('//', '/')
        
        if not os.path.isfile(kmspony):
            protokmsponies = '/var/cache/ponysay/protokmsponies/'
            protokmspony = (protokmsponies + pony).replace('//', '/')
            
            protokmsponydir = protokmspony[:protokmspony.rindex('/')]
            kmsponydir      =      kmspony[:     kmspony.rindex('/')]
            
            _protokmspony = '\'' + protokmspony.replace('\'', '\'\\\'\'') + '\''
            _kmspony      = '\'' +      kmspony.replace('\'', '\'\\\'\'') + '\''
            _pony         = '\'' +         pony.replace('\'', '\'\\\'\'') + '\''
            
            if not os.path.isfile(protokmspony):
                if not os.path.isdir(protokmsponydir):
                    os.makedirs(protokmsponydir)
                if not os.system('ponysay2ttyponysay < ' + _pony + ' > ' + _protokmspony) == 0:
                    sys.stderr.write('Unable to run ponysay2ttyponysay successfully, you need util-say for KMS support\n')
                    exit(1)
            
            if not os.path.isdir(kmsponydir):
                os.makedirs(kmsponydir)
            if not os.system('tty2colourfultty -e -p ' + palette + ' < ' + _protokmspony + ' > ' + _kmspony) == 0:
                sys.stderr.write('Unable to run tty2colourfultty successfully, you need util-say for KMS support\n')
                exit(1)
        
        return kmspony



ARGUMENTLESS = 0
ARGUMENTED = 1
VARIADIC = 2
'''
Simple argument parser
'''
class ArgParser():
    '''
    Constructor.
    The short description is printed on same line as the program name
    '''
    def __init__(self, program, description, usage, longdescription = None):
        self.__program = program
        self.__description = description
        self.__usage = usage
        self.__longdescription = longdescription
        self.__arguments = []
        self.opts = {}
        self.optmap = {}
    
    
    '''
    Add option that takes no arguments
    '''
    def add_argumentless(self, alternatives, help = None):
        ARGUMENTLESS
        self.__arguments.append((ARGUMENTLESS, alternatives, None, help))
        stdalt = alternatives[0]
        self.opts[stdalt] = None
        for alt in alternatives:
            self.optmap[alt] = (stdalt, ARGUMENTLESS)
    
    '''
    Add option that takes one argument
    '''
    def add_argumented(self, alternatives, arg, help = None):
        self.__arguments.append((ARGUMENTED, alternatives, arg, help))
        stdalt = alternatives[0]
        self.opts[stdalt] = None
        for alt in alternatives:
            self.optmap[alt] = (stdalt, ARGUMENTED)
    
    '''
    Add option that takes all following argument
    '''
    def add_variadic(self, alternatives, arg, help = None):
        self.__arguments.append((VARIADIC, alternatives, arg, help))
        stdalt = alternatives[0]
        self.opts[stdalt] = None
        for alt in alternatives:
            self.optmap[alt] = (stdalt, VARIADIC)
    
    
    '''
    Parse arguments
    '''
    def parse(self, argv = sys.argv):
        self.argcount = len(argv) - 1
        self.files = []
        
        argqueue = []
        optqueue = []
        deque = []
        for arg in argv[1:]:
            deque.append(arg)
        
        dashed = False
        tmpdashed = False
        get = 0
        dontget = 0
        
        def unrecognised(arg):
            sys.stderr.write('%s: warning: unrecognised option %s\n' % (self.__program, arg))
        
        while len(deque) != 0:
            arg = deque[0]
            deque = deque[1:]
            if (get > 0) and (dontget == 0):
                get -= 1
                argqueue.append(arg)
            elif tmpdashed:
                self.files.append(arg)
                tmpdashed = False
            elif dashed:        self.files.append(arg)
            elif arg == '++':   tmpdashed = True
            elif arg == '--':   dashed = True
            elif (len(arg) > 1) and ((arg[0] == '-') or (arg[0] == '+')):
                if (len(arg) > 2) and ((arg[:2] == '--') or (arg[:2] == '++')):
                    if dontget > 0:
                        dontget -= 1
                    elif (arg in self.optmap) and (self.optmap[arg][1] == ARGUMENTLESS):
                        optqueue.append(arg)
                        argqueue.append(None)
                    elif '=' in arg:
                        arg_opt = arg[:arg.index('=')]
                        if (arg_opt in self.optmap) and (self.optmap[arg_opt][1] >= ARGUMENTED):
                            optqueue.append(arg_opt)
                            argqueue.append(arg[arg.index('=') + 1:])
                            if self.optmap[arg_opt][1] == VARIADIC:
                                dashed = True
                        else:
                            unrecognised(arg)
                    elif (arg in self.optmap) and (self.optmap[arg][1] == ARGUMENTED):
                        optqueue.append(arg)
                        get += 1
                    elif (arg in self.optmap) and (self.optmap[arg][1] == VARIADIC):
                        optqueue.append(arg)
                        argqueue.append(None)
                        dashed = True
                    else:
                        unrecognised(arg)
                else:
                    sign = arg[0]
                    i = 1
                    n = len(arg)
                    while i < n:
                        narg = sign + arg[i]
                        i += 1
                        if (narg in self.optmap):
                            if self.optmap[narg][1] == ARGUMENTLESS:
                                optqueue.append(narg)
                                argqueue.append(None)
                            elif self.optmap[narg][1] == ARGUMENTED:
                                optqueue.append(narg)
                                nargarg = arg[i:]
                                if len(nargarg) == 0:
                                    get += 1
                                else:
                                    argqueue.append(nargarg)
                                break
                            elif self.optmap[narg][1] == VARIADIC:
                                optqueue.append(narg)
                                nargarg = arg[i:]
                                argqueue.append(nargarg if len(nargarg) > 0 else None)
                                dashed = True
                                break
                        else:
                            unrecognised(arg)
            else:
                self.files.append(arg)
        
        i = 0
        n = len(optqueue)
        while i < n:
            opt = optqueue[i]
            arg = argqueue[i]
            i += 1
            opt = self.optmap[opt][0]
            if (opt not in self.opts) or (self.opts[opt] is None):
                self.opts[opt] = []
            self.opts[opt].append(arg)
        
        for arg in self.__arguments:
            if (arg[0] == VARIADIC):
                varopt = self.opts[arg[1][0]]
                if varopt is not None:
                    additional = ','.join(self.files).split(',') if len(self.files) > 0 else []
                    if varopt[0] is None:
                        self.opts[arg[1][0]] = additional
                    else:
                        self.opts[arg[1][0]] = varopt[0].split(',') + additional
                    self.files = []
                    break
        
        self.message = ' '.join(self.files) if len(self.files) > 0 else None
    
    
    '''
    Prints a colourful help message
    '''
    def help(self):
        print('\033[1m%s\033[21m %s %s' % (self.__program, '-' if linuxvt else '—', self.__description))
        print()
        if self.__longdescription is not None:
            print(self.__longdescription)
            print()
        print()
        
        print('\033[1mUSAGE:\033[21m', end='')
        first = True
        for line in self.__usage.split('\n'):
            if first:
                first = False
            else:
                print('    or', end="")
            print('\t%s' % (line))
        print()
        
        print('\033[1mSYNOPSIS:\033[21m')
        print()
        for opt in self.__arguments:
            opt_type = opt[0]
            opt_alts = opt[1]
            opt_arg = opt[2]
            opt_help = opt[3]
            if opt_help is None:
                continue
            for opt_alt in opt_alts:
                if opt_alt is opt_alts[-1]:
                    print('\t' + opt_alt, end='')
                    if   opt_type == ARGUMENTED:  print(' \033[4m%s\033[24m'      % (opt_arg))
                    elif opt_type == VARIADIC:    print(' [\033[4m%s\033[24m...]' % (opt_arg))
                    else:                         print()
                else:
                    print('\t\033[2m' + opt_alt + '\033[22m')
            first = True
            for line in opt_help.split('\n'):
                if first:
                    first = False
                    print('\t\t\033[32;1m%s\033[21;39m' % (line))
                else:
                    print('\t\t%s' % (line))
            print()
        
        print()



usage_saythink = '\033[34;1m(ponysay | ponythink)\033[21;39m'
usage_wrap     = '--wrap \033[4mCOLUMN\033[24m'
usage_listhelp = '(--list | ---altlist | --version | --help)'
usage_file     = '[--pony \033[4mPONY\033[24m]... ([--] \033[4mmessage\033[24m | <<<\033[4mmessage\033[24m)'
usage_quote    = '--quote [\033[4mPONY\033[24m...]'

usage = '%s %s\n%s [%s] %s\n%s [%s] %s' % (usage_saythink, usage_listhelp,
                                           usage_saythink, usage_wrap, usage_file,
                                           usage_saythink, usage_wrap, usage_quote)

usage = usage.replace('\033[', '\0')
for sym in ('[', ']', '(', ')', '|', '...'):
    usage = usage.replace(sym, '\033[2m' + sym + '\033[22m')
usage = usage.replace('\0', '\033[')

'''
Argument parsing
'''
opts = ArgParser(program     = 'ponythink' if isthink else 'ponysay',
                 description = 'cowsay wrapper for ponies',
                 usage       = usage,
                 longdescription =
'''Ponysay displays an image of a pony saying some text provided by the user.
If \033[4mmessage\033[24m is not provided, it accepts standard input. For an extensive
documentation run `info ponysay`, or for just a little more help than this
run `man ponysay`. Ponysay has so much more to offer than described here.''')

opts.add_argumentless(['--quoters'])
opts.add_argumentless(['--onelist'])

opts.add_argumentless(['-h', '--help'],                      help = 'Print this help message.')
opts.add_argumentless(['-v', '--version'],                   help = 'Print the version of the program.')
opts.add_argumentless(['-l', '--list'],                      help = 'List pony files.')
opts.add_argumentless(['-L', '--altlist'],                   help = 'List pony files with alternatives.')
opts.add_argumented(  ['-W', '--wrap'],     arg = "COLUMN",  help = 'Specify the column when the message should be wrapped.')
opts.add_argumented(  ['-f', '--pony'],     arg = "PONY",    help = 'Select a pony.\nEither a file name or a pony name.')
opts.add_variadic(    ['-q', '--quote'],    arg = "PONY",    help = 'Select a ponies which will quote themself.')

opts.parse()



'''
Replacement for cowsay
'''
class Backend():
    '''
    Constructor
    Takes message [string], ponyfile [filename string], wrapcolumn [None or an int] and width [None or an int]
    '''
    def __init__(self, message, ponyfile, wrapcolumn, width):
        self.message = message
        self.ponyfile = ponyfile
        self.wrapcolumn = wrapcolumn
        self.width = width
        
        self.link = {'\\' : '\\', '/' : '/'} if not isthink else {'\\' : 'o', '/' : 'o'}
        
        self.output = None
        self.pony = None
    
    
    '''
    Process all data
    '''
    def parse(self):
        self.__expandMessage()
        self.__loadFile()
        self.__processPony()
        self.__truncate()
    
    
    def __expandMessage(self):
        lines = self.message.split('\n')
        buf = ''
        for line in lines:
            (i, n, x) = (0, len(line), 0)
            while i < n:
                c = line[i]
                i += 1
                if c == '\033':
                    colour = self.__getcolour(line, i - 1)
                    i += len(colour) - 1
                    buf += colour
                elif c == '\t':
                    nx = 8 - (x & 7)
                    buf += ' ' * nx
                    x += nx
                else:
                    buf += c
                    x += 1
            buf += '\n'
        self.message = buf[:-1]
    
    
    def __loadFile(self):
        ponystream = None
        try:
            ponystream = open(self.ponyfile, 'r')
            self.pony = ''.join(ponystream.readlines())
        finally:
            if ponystream is not None:
                ponystream.close()
    
    
    def __truncate(self):
        if self.width is None:
            return
        lines = self.output.split('\n')
        self.output = ''
        for line in lines:
            (i, n, x) = (0, len(line), 0)
            while i < n:
                c = line[i]
                i += 1
                if c == '\033':
                    colour = self.__getcolour(line, i - 1)
                    i += len(colour) - 1
                    self.output += colour
                else:
                    if x < self.width:
                        self.output += c
                        x += 1
            self.output += '\n'
        self.output = self.output[:-1]
    
    
    def __processPony(self):
        self.output = ''
        
        variables = {'' : '$'}
        for key in self.link:
            variables[key] = self.link[key]
        
        indent = 0
        dollar = None
        
        (i, n) = (0, len(self.pony))
        while i < n:
            c = self.pony[i]
            if c == '\t':
                n += 8 - (indent & 7)
                ed = ' ' * (7 - (indent & 7))
                c = ' '
                self.pony = self.pony[:i] + ed + self.pony[i:]
            i += 1
            if c == '$':
                if dollar is not None:
                    if '=' in dollar:
                        name = dollar[:find('=')]
                        value = dollar[find('=') + 1:]
                        variables[name] = value
                    elif (len(dollar) < 7) or not (dollar[:7] == 'balloon'):
                        if dollar in ('\\', '/'):
                            i += len(variables[dollar]) - 1
                        lines = variables[dollar].split('\n')
                        firstvarline = True
                        for line in lines:
                            if firstvarline:
                                firstvarline = False
                            else:
                                indent = 0
                                self.output = '\n'
                            self.output += line
                            indent += len(line)
                    else:
                        (w, h) = (0, 0)
                        props = dollar[7:]
                        if len(props) == 0:
                            if ',' in props:
                                if props[0] is not ',':
                                    w = int(props[:props.index(',')])
                                h = int(props[props.index(',') + 1:])
                            else:
                                w = int(props)
                        balloon = self.__getballoon(w, h, indent).split('\n')
                        balloonpre = '\n' + (' ' * indent)
                        self.output += balloon[0]
                        for line in balloon[1:]:
                            self.output += balloonpre;
                            self.output += line;
                        indent = 0
                    dollar = None
                else:
                    dollar = ''
            elif dollar is not None:
                if c == '\033':
                    c = self.pony[i]
                    i += 1
                dollar += c
            elif c == '\033':
                colour = self.__getcolour(self.pony, i - 1)
                self.output += colour
                i += len(colour) - 1
            elif c == '\n':
                self.output += c
                indent = 0
            else:
                self.output += c
                indent += 1
    
    
    def __getcolour(self, input, offset):
        (i, n) = (offset, len(input))
        rc = input[i]
        i += 1
        if i == n: return rc
        c = input[i]
        i += 1
        rc += c
        
        if c == ']':
            if i == n: return rc
            c = input[i]
            i += 1
            rc += c
            if c == 'P':
                di = 0
                while (di < 7) and (i < n):
                    c = input[i]
                    i += 1
                    di += 1
                    rc += c
        elif c == '[':
            while i < n:
                c = input[i]
                i += 1
                rc += c
                if (c == '~') or (('a' <= c) and (c <= 'z')) or (('A' <= c) and (c <= 'Z')):
                    break
        
        return rc
    
    
    def __getballoon(self, width, height, left):
        wrap = None
        if self.wrapcolumn is not None:
            wrap = self.wrapcolumn - left
        
        msg = self.message
        if wrap is not None:
            msg = self.__wrapMessage(msg, wrap)
        lines = msg.split('\n')
        h = 4 + len(lines)
        w = 6 + len(max(lines, key = len))
        if w < width:   w = width
        if h < height:  h = height
        
        rc = '/' + '-' * (w - 2) + '\\\n'
        rc += '|' + ' ' * (w - 2) + '|\n'
        for line in lines:
            rc += '|  ' + line + ' ' * (w - len(line) - 6) + '  |\n'
        rc += '|' + ' ' * (w - 2) + '|\n'
        rc += '\\' + '-' * (w - 2) + '/'
        
        return rc
    
    
    def __wrapMessage(self, message, wrap):
        lines = message.split('\n')
        buf = ''
        for line in lines:
            b = [None] * len(line)
            map = {}
            (bi, cols, w) = (0, 0, wrap)
            (indent, indentc) = (-1, 0)
            
            (i, n) = (0, len(line))
            while i <= n:
                d = None
                if i != n:
                    d = line[i]
                i += 1
                if d == '\033':
                    b[bi] = d
                    bi += 1
                    b[bi] = line[i]
                    d = line[i]
                    bi += 1
                    i += 1
                    if d == '[':
                        while True:
                            b[bi] = line[i]
                            d = line[i]
                            bi += 1
                            i += 1
                            if (('a' <= d) and (d <= 'z')) or (('A' <= d) and (d <= 'Z')) or (d == '~'):
                                break
                    elif d == ']':
                        b[bi] = line[i]
                        d = line[i]
                        bi += 1
                        i += 1
                        if d == 'P':
                            for j in range(0, 7):
                                b[bi] = line[i]
                                bi += 1
                                i += 1
                elif (d is not None) and (d != ' '):
                    if indent == -1:
                        indent = i - 1
                        for j in range(0, indent):
                            if line[j] == ' ':
                                indentc += 1
                    b[bi] = d
                    bi += 1
                    cols += 1
                    map[cols] = bi
                else:
                    mm = 0
                    while (w > 8) and (cols > w + 3):
                        mm += w - 1
                        m = map[mm]
                        for bb in b[:m]:
                            buf += bb
                        buf += '-\n'
                        cols -= w - 1
                        m += w -1
                        bi -= m
                        bb = b[m:]
                        for j in range(0, bi):
                            b[j] = bb[j]
                        w = wrap
                        if indent != -1:
                            buf += line[:indent]
                            w -= indentc
                    if cols > w:
                        buf += '\n'
                        w = wrap
                        if indent != -1:
                            buf += line[:indent]
                            w -= indentc
                    for bb in b[:bi]:
                        buf += bb
                    w -= cols
                    cols = 0
                    bi = 0
                    if d == -1:
                        i += 1
                    else:
                        if w > 0:
                            buf += ' '
                            w -= 1
                        else:
                            buf += '\n'
                            w = wrap
                            if indent != -1:
                                buf + line[:indent]
                                w -= indentc
            
            buf += '\n'
        return buf[:-1]



'''
Start the program from ponysay.__init__ if this is the executed file
'''
if __name__ == '__main__':
    Ponysay(opts)
