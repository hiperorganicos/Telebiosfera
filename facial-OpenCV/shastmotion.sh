#! /bin/sh
# /etc/init.d/shastmotion
#

# Some things that run always
python /home/MotionDetection/motion.py

# Carry out specific functions when asked to by the system
case "$1" in
  start)
    echo "Starting script shastmotion "
    python /home/MotionDetection/motion.py
    echo "Could do more here"
    ;;
  stop)
    echo "Stopping script blah"
    echo "Could do more here"
    ;;
  *)
    echo "Usage: /etc/init.d/blah {start|stop}"
    exit 1
    ;;
esac

exit 0
