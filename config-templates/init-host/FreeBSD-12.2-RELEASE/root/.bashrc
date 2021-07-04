# Source global definitions
if [ -f /usr/local/etc/bashrc ] 
then
  . /usr/local/etc/bashrc
fi

PS1="\[\e[1;31m\][\u@\h:\W]\$\[\e[0m\] "
