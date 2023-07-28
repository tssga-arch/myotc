Command Line utilities
======================

myotc
-----

MyOTC automation script

.. argparse::
   :filename: ../src/cli.py
   :func: parser

urotc
-----

Restricted automation script

.. argparse::
   :filename: ../src/urotc.py
   :func: cliparser

hasher
------

Calculate password hashes

.. argparse::
   :filename: ../src/hasher.py
   :func: passwdcalc_cli

ypp
---

YAML Pre-Processor utility

.. argparse::
   :filename: ../src/ypp.py
   :func: cmd_cli

Pre-processor syntax
....................

* To define variables:

  * ``#define key value``

* To use a variable:

  * ``{key}``
  * note that it can be embedded in a string, e.g. ``something {key} other``

* Escape variable:

  * ``{{ ... }}``
  * Double brackets, i.e. ``{{`` and ``}}`` are replaced by single brackets.

* password generator:

  * ``$PWGEN:store:len$`` : Generate a clear text password  of ``len`` characters (and save it as ``store``)
  * ``$PWGEN:store:MD5:len$`` : Generate a password and encode it using UNIX MD5 hash.
  * ``$PWGEN:store:SHA256:len$``
  * ``$PWGEN:store:SHA512:len$`` : Generate a password and encode it using SHA256 or SHA512 hashes.
  * ``$PWGEN:store:vnc:len$`` : Generate a password and encode it using VNC password format.
  * ``$$ PWGEN ...`` :  Escape password generator

* ssh key generator:

  * ``$KEYGEN:file:pub`` : Generate public keypair and save it to ``file``.  Output public key.
  * ``$KEYGEN:file:priv`` : Generate public keypair and save it to ``file``.  Output private key.
  * ``$$KEYGEN`` : Escape key generator

PWGEN will save clear text version of passwords to:

* ``_secrets.yaml`` or
* ``../secrets/_secrets.yaml`` or
* whatever is defined as ``_secrets_file_``.

KEYGEN will save public/private key pairs as files in directory:

* ``_keys_`` or
* ``../secrets`` or
* whatever is defined as ``_ssh_key_store_``.

Pre-processor conditionals:

* ``#ifdef <variable>``
* ``#ifndef <variable>``
* ``#else``
* ``#endif``

Additional pre-processor statements:

* ``#exec <command>`` : will execute the ``command`` and its
  output will be included into the YAML file.  File structure
  is preserved.
* ``#error <msg>`` : Display ``msg`` and aborts execution
* ``#warn <msg>`` : Display ``msg``

