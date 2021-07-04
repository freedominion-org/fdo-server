# Source global definitions
if [ -f /usr/local/etc/bashrc ]
then
  . /usr/local/etc/bashrc
fi

root () {
  su - toor
}

PS1="\[\e[1;32m\][\u@\h:\[\e[0m\]\W\e[1;32m\]]\$\e[0m\] "
