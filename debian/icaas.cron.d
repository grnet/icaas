#
# cron.d/icaas -- schedules periodic checks for agent timeouts
#

SHELL=/bin/sh
PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin

# Check every 10 minutes if there are agents that exceeded the timeout period
*/10 * * * * root [ -x /usr/bin/icaas-manage ] && /usr/bin/icaas-manage timeout
