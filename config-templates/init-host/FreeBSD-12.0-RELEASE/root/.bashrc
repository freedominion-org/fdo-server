# Source global definitions
if [ -f /usr/local/etc/bashrc ] 
then
  . /usr/local/etc/bashrc
fi

PS1="\[\e[1;31m\][\u@\h:\[\e[0m\]\W\[\e[1;31m\]]#\[\e[0m\] "
