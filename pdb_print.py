def __debugger_p(name, o):
	global __debugger_p
	del __debugger_p # don't leave this hanging around in the scope being debugged

	#print("ARGS '%*'")

	IGNORE_BUILTIN_FUNCS = True
	IGNORE_METHOD_WRAPPERS = True
	DONT_RECURSE_TYPES = (int, float, complex, bool, str, range, set, bytes, bytearray, memoryview, type)
	list_types = (tuple,list,set,frozenset)
	output = ""

	def setting(fallback, key:str, arg:str=None, default:str=None):
		t = type(fallback)
		if arg and not arg.startswith("%"):
			return t(arg);
		if default and not default.startswith("%"):
			return t(default);
		if "__debugger_settings" in globals():
			settings = globals()["__debugger_settings"]
			if key in settings:
				return t(settings.get(key))
			raise KeyError(f"'{key}' not in setting")
		return fallback

	def try_arg(value, s, name, uses_curly_braces=False):
		def find_slice(s, start, end):
			a = s.rindex(start) + len(start)
			b = s.find(end, a)
			if b != -1:
				return s[a:b]
			else:
				return s[a:]
		if (" " + name + "=") in s:
			t = type(value)
			try:
				if uses_curly_braces:
					try:
						return t(find_slice(s, " " + name + "={", "}"))
					except:
						pass
				return t(find_slice(s, " " + name + "=", " "))
			except:
				pass
		return value

	setting_max_depth = setting(0, "max_depth")
	default_max_depth = try_arg(setting_max_depth, "%*", "default_depth")
	max_depth = try_arg(default_max_depth, "%*", "depth")
	max_list_len = try_arg(setting(10, "max_list_len"), "%*", "listlen")
	max_line_width = try_arg(setting(120, "max_line_width"), "%*", "linelen")
	function_recursion = try_arg(setting(0, "function_recursion"), "%*", "function_recursion")
	filter = try_arg("", "%*", "filter", True)

	def match_filter(s):
		return filter in s

	def debug_print(s, end=chr(10)):
		nonlocal output
		output += s + end

	def debug_value(a, no_replace=False):
		if isinstance(a, (str, dict) + list_types):
			s = str(a)
			l = len(a)
			quote = "'" if isinstance(a, str) else ""
			has_newlines = False
			if not no_replace:
				s = s.replace(chr(10), chr(92)+"n").replace(chr(13), chr(92)+"r").replace(chr(9), chr(92)+"t")
			elif chr(10) in s:
				has_newlines = True
				quote = '""' '"'
			strlen = len(s)

			t = type(a).__name__
			debug_print(f" : {f'{t}[{l}]':8} = ", end="")
			if has_newlines:
				debug_print("")
			debug_print(f"{quote}{s}{quote}")
			if has_newlines:
				debug_print("")
		else:
			debug_print(f" : {type(a).__name__:8}", end="")
			try:
				debug_print(f" = {a}")
			except Exception as e:
				debug_print(f"*** {type(e).__name__}: {e}")
				return

	def debug_attr(prefix:str, o, attr):
		if isinstance(attr, str) and attr.startswith("__debugger_"):
			return None, None
		a = exp = None
		if isinstance(o, dict):
			a = o.get(attr)
		else:
			try:
				a = getattr(o, attr)
			except Exception as e:
				exp = f"*** {type(e).__name__}: {e}"
		if IGNORE_BUILTIN_FUNCS and a and type(a).__name__ == "builtin_function_or_method":
			return None, None
		if IGNORE_BUILTIN_FUNCS and a and type(a).__name__ == "method-wrapper":
			return None, None
		k = str(attr)
		nonlocal output
		old_len = len(output)
		debug_print(f"{prefix + k:<20}", end="")
		if exp: debug_print(exp)
		else: debug_value(a)
		if not match_filter(output[old_len:]): output = output[:old_len]
		elif len(output) - old_len > max_line_width: output = output[:old_len + max_line_width - 20] + f"... (do 'linelen={len(output) - old_len}'){chr(10)}"
		if exp: return None, None
		if k.startswith('__') or len(prefix) > 50 or isinstance(a, DONT_RECURSE_TYPES) or type(a).__name__ == "module":
			return None, None
		return prefix + str(attr) + ".", a

	def recurse(prefix, o, d):
		if d > max_depth: return
		d += 1
		if prefix == "locals().": prefix = ""
		if isinstance(o, (dict)):
			for k in o:
				p,a = debug_attr(prefix,o,k)
				if a: recurse(p,a,d)
		elif isinstance(o, list_types):
			count=n=0
			for i in o:
				if count >= max_list_len:
					if max_list_len > 0:
						debug_print(f"(+{len(o) - max_list_len} more; use 'listlen={len(o)}' to show everything)")
					break
				p=f"{prefix.rstrip('.')}[{n}]"
				n+=1

				nonlocal output
				old_len = len(output)
				debug_print(f"{p:<20}", end="")
				debug_value(i)
				if not match_filter(output[old_len:]): output = output[:old_len]
				else: count+=1
				if not isinstance(i, DONT_RECURSE_TYPES):
					recurse(p+'.',i,d)
		elif callable(o) and d > 1 and not function_recursion:
			return
		else:
			for k in dir(o):
				p,a = debug_attr(prefix,o,k)
				if a: recurse(p,a,d)

	try:
		empty_arguments = name.startswith("%")
		if empty_arguments:
			name = ""
			prefix = ""
		else:
			prefix = name + "."
			debug_print(f"{name:<20}", end="")
			if isinstance(o, str):
				debug_value(o, no_replace=True)
			elif isinstance(o, list_types) and max_depth == 0:
				old_list_len = max_list_len
				max_list_len = max(10, max_list_len)
				debug_value(o)
				max_list_len = old_list_len
			elif not isinstance(o, (dict,) + list_types) or max_depth == 0:
				debug_value(o)
			else:
				debug_print(f" : {type(o).__name__}")
		recurse(prefix, o, 0)
		print(output, end="")
	except:
		#import pdb; pdb.post_mortem()
		raise

'''SETTINGS'''
def __debugger_set(key:str, value:str = "%"):
	global __debugger_settings, __debugger_set
	del __debugger_set # don't leave this hanging around in the scope being debugged

	if "__debugger_settings" not in globals():
		__debugger_settings = {
		"max_depth":"1",
		"max_list_len":"10",
		"max_line_width":"120",
		"function_recursion": "0",
		}
	if key.startswith("%"):
		result = ""
		for k,v in __debugger_settings.items():
			result += f"{k} = {v}{chr(10)}"
		return result.strip()
	if not key in __debugger_settings:
		raise KeyError(f"{key} unknown setting")

	if not value.startswith("%"):
		__debugger_settings[key] = value

	result = __debugger_settings.get(key)
	return result
'''END'''

class Test:
	def __repr__(self):
		raise Exception("Test exception in '__repr__'")
	def __str__(self):
		raise Exception("Test exception in '__str__'")

__debugger_p("test", Test()) # make sure we don't crash before saving the changes
print("Tests passed! :)")

from inspect import getsourcefile
from os.path import abspath
this_file_path = abspath(getsourcefile(lambda:0))
print(f"This file {this_file_path}")
with open(this_file_path, "r") as f:
	lines = f.readlines()

p_command_end = lines.index("'''SETTINGS'''\n")
p_command = lines[:p_command_end] + ["__debugger_p('''(%1)'''[1:-1], eval('''(%1)'''[1:-1]) if not '''(%1)'''.startswith('(%') else locals())"]

set_command_end = lines.index("'''END'''\n")
set_command = lines[p_command_end+1:set_command_end] + ["print(__debugger_set('%1', '%2'))"]

def sanitize(lines):
	result = '\\n'.join(lines)
	for i in range(len(lines)-1):
		l = lines[i]
		if '"""' in l:
			raise ValueError(f'\'"""\' encountered {l}')
		if "'''" in l:
			raise ValueError(f"\"'''\" encountered {l}")

	result = result.replace("\n", "")
	result = result.replace("\r", "")
	result = result.replace("\t", "\\t")
	return 'exec("""' + result + '""")'

with open('.pdbrc', 'w') as f:
	f.write(f'''
alias locals p locals()
alias pl p locals() %*
alias plr p locals() depth=5 listlen=0 %*
alias pr p %1 depth=9 listlen=0 %*
alias ls p %1 depth=0 %*
alias lsr p %1 depth=9 %*
alias ps p self depth=%1 default_depth=1 %*
alias divider exec("""print("-" * 50)""") ;; ls
alias h l ;; divider
alias s step ;; h
alias n next ;; h
alias c continue ;; h
alias w where ;; h
alias ww print("-" * 50) ;; w
alias u up ;; ww
alias d down ;; ww
alias r return ;; ww
alias filter p %% depth=9 filter={{%*}} function_recursion=1
alias doc p %1 depth=9 filter={{.__doc__}} function_recursion=1 listlen=0 %*
alias docs doc %% %*

alias depth set max_depth %1
alias strlen set max_line_width %1
alias linelen set max_line_width %1
alias listlen set max_list_len %1

alias p {sanitize(p_command)}

alias set {sanitize(set_command)}
''')




### Stuff to test with ###

def rtfm():
	"""What's up doc?"""

a = {'c':'d', 'reccc':sanitize}
b = {'a':a, 'rtfm':rtfm, 'settt':sanitize}
l = [0, 1, a, b, 2, 3]
n = 5
hmm = {"very":{"deep":{"recursion":{"can":{"be":{"printed":{"with":"lsr N"}}}}}}}

breakpoint()

def test():
	"""Hello from a function"""
	breakpoint()
test()

breakpoint()
