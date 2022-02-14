#
# System-wide .login file for csh(1).
#
# For the setting of languages and character sets please see
# login.conf(5) and in particular the charset and lang options.
# For full locales list check /usr/share/locale/*
#
# Check system messages
# msgs -q
# Allow terminal messages
# mesg y

setenv LANG HOST_LOCALE
setenv MM_CHARSET HOST_CHARSET

setenv TZ HOST_TIMEZONE
