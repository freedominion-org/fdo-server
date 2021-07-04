# Source global definitions
if [ -f /usr/local/etc/bashrc ]
then
  . /usr/local/etc/bashrc
fi

root () {
  su - toor
}

PS1="\[\e[1;32m\][\u@\h:\W]\$\[\e[0m\] "
