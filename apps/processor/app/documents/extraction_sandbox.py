"""Linux process restrictions for untrusted documents; fail closed if unavailable.

Landlock confines filesystem access, libseccomp denies Internet sockets. Both
are inherited by local OCR/conversion children and require no extra capabilities.
"""
import ctypes
import errno
import os
from pathlib import Path
import resource
import sysconfig


def restrict(directory, *, memory_mb, seconds, output_bytes):
    resource.setrlimit(resource.RLIMIT_AS, (memory_mb * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (output_bytes,) * 2)
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:  # PR_SET_NO_NEW_PRIVS
        raise RuntimeError('extraction_sandbox_unavailable')

    # Linux syscall numbers are shared by supported amd64/arm64 container images.
    abi = libc.syscall(444, 0, 0, 1)  # landlock_create_ruleset VERSION
    if abi < 1:
        raise RuntimeError('extraction_filesystem_sandbox_unavailable')
    access = (1 << (15 if abi >= 3 else 14 if abi >= 2 else 13)) - 1
    class Ruleset(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]
    class PathRule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]
    ruleset = Ruleset(access)
    descriptor = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
    if descriptor < 0:
        raise RuntimeError('extraction_filesystem_sandbox_unavailable')
    try:
        readonly = 1 | (1 << 2) | (1 << 3)  # execute, read-file, read-directory
        paths = {str(Path(directory).resolve()): access}
        # Hosted and virtualenv Python libraries may live outside /usr. Permit
        # only their installation directories, not the prefix or caller sys.path.
        runtime_paths = tuple(sysconfig.get_path(name) for name in ('stdlib', 'platstdlib', 'purelib', 'platlib'))
        for value in ('/usr', '/lib', '/lib64', '/etc/fonts', '/etc/libreoffice', '/etc/ld.so.cache', '/etc/passwd',
                      '/etc/group', '/etc/nsswitch.conf', '/etc/localtime', '/etc/os-release', '/proc/self',
                      # Debian packages link these runtime registries outside /usr.
                      # Resolve only these installation paths and keep them read-only.
                      '/usr/lib/libreoffice/share/prereg/bundled',
                      '/usr/lib/libreoffice/share/uno_packages/cache',
                      *runtime_paths):
            if Path(value).exists():
                paths[str(Path(value).resolve())] = readonly
        paths['/dev/null'] = (1 << 1) | (1 << 2)
        paths['/dev/urandom'] = 1 << 2
        for path, rights in paths.items():
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                if not Path(path).is_dir():
                    rights &= 1 | (1 << 1) | (1 << 2) | (1 << 14)
                rule = PathRule(rights, fd)
                if libc.syscall(445, descriptor, 1, ctypes.byref(rule), 0) != 0:
                    raise RuntimeError('extraction_filesystem_sandbox_unavailable')
            finally:
                os.close(fd)
        if libc.syscall(446, descriptor, 0) != 0:
            raise RuntimeError('extraction_filesystem_sandbox_unavailable')
    finally:
        os.close(descriptor)

    seccomp = ctypes.CDLL('libseccomp.so.2')
    seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    seccomp.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int,
                                             ctypes.c_uint, ctypes.c_void_p]
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
    class Comparison(ctypes.Structure):
        _fields_ = [('arg', ctypes.c_uint), ('op', ctypes.c_int),
                    ('a', ctypes.c_uint64), ('b', ctypes.c_uint64)]
    context = seccomp.seccomp_init(0x7FFF0000)  # SCMP_ACT_ALLOW
    if not context:
        raise RuntimeError('extraction_network_sandbox_unavailable')
    try:
        deny = 0x00050000 | errno.EPERM
        comparison = Comparison(0, 1, 1, 0)  # socket domain != AF_UNIX
        number = seccomp.seccomp_syscall_resolve_name(b'socket')
        if seccomp.seccomp_rule_add_array(context, deny, number, 1, ctypes.byref(comparison)) != 0:
            raise RuntimeError('extraction_network_sandbox_unavailable')
        # Landlock deliberately does not mediate access(2). LibreOffice otherwise
        # sees /tmp writable and ignores its explicit OSL_SOCKET_PATH. Fail this
        # legacy write-access probe closed, so IPC falls back to the owned path.
        # Real open/write permissions remain governed by Landlock, not this probe.
        number = seccomp.seccomp_syscall_resolve_name(b'access')
        write_probe = Comparison(1, 7, os.W_OK, os.W_OK)  # MASKED_EQ
        if number >= 0 and seccomp.seccomp_rule_add_array(context, deny, number, 1, ctypes.byref(write_probe)) != 0:
            raise RuntimeError('extraction_filesystem_sandbox_unavailable')
        for name in (b'ptrace', b'mount', b'umount2', b'unshare', b'setns', b'bpf'):
            number = seccomp.seccomp_syscall_resolve_name(name)
            if number >= 0 and seccomp.seccomp_rule_add_array(context, deny, number, 0, None) != 0:
                raise RuntimeError('extraction_network_sandbox_unavailable')
        if seccomp.seccomp_load(context) != 0:
            raise RuntimeError('extraction_network_sandbox_unavailable')
    finally:
        seccomp.seccomp_release(context)
