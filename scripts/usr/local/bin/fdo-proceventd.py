#!/usr/local/bin/python2.7

# Runs on FreeBSD 10.1
# Additional FreeBSD ports/packages: py-psycopg2
# Install from pip: python-daemon

import logging
import time
import smtplib
from smtplib import SMTPException
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from daemon import runner
import psycopg2
import psycopg2.extras

class App():

    def __init__(self):

        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/proceventd/stdout.log'
        self.stderr_path = '/var/log/proceventd/stderr.log'
        self.pidfile_path =  '/var/run/proceventd.pid'
        self.pidfile_timeout = 5

        self.mailServer = "smtp.example.net"

    def run(self):

        #logger.debug("Debug message")
        logger.info("Starting proceventd")
        #logger.warn("Warning message")
        #logger.error("Error message")

        dbUsername = "DB_USERNAME"
        dbPassword = "DB_PASSWORD"

        while True:
            while not self.openDatabase("pgsql.example.net","freedominion.org",dbUsername,dbPassword):
                time.sleep(30)

            while True:
                self.pubHolProcess()
                self.userTableChangeProcess()
                self.endOfYearProcess()
                time.sleep(60)

    def endOfYearProcess(self):

        logger.debug("Entered endOfYearProcess (self)")

        query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query.execute("select extract(year from now()) as year")
        row = query.fetchone()
        query.close()
        thisYear = int(row['year'])
        lastYear = thisYear - 1

        query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query.execute("select user_id,annual_leave_remaining,annual_leave_carry from user_annual_leave where year = " + str(lastYear) + " and carry_processed = false")
 
        resultset = query.fetchall()
        query.close()
 
        for row in resultset:

            logger.debug("Entered endOfYearProcess.forloop (self)")

            userId = row['user_id']
            leaveRemaining = row['annual_leave_remaining']
            maxCarry = row['annual_leave_carry']

            if leaveRemaining > maxCarry:
                carryDays = maxCarry
            else:
                carryDays = leaveRemaining

            logger.debug("carryDays: " + str(carryDays))

            queryString1 = "update user_annual_leave set annual_leave_remaining  = annual_leave_remaining - " + str(carryDays) + " where user_id = " + str(userId) + " and year = " + str(lastYear) 
            queryString2 = "update user_annual_leave set annual_leave_remaining  = annual_leave_remaining + " + str(carryDays) + " where user_id = " + str(userId) + " and year = " + str(thisYear) 
            queryString3 = "update user_annual_leave set annual_leave_lieu  = annual_leave_lieu + " + str(carryDays) + " where user_id = " + str(userId) + " and year = " + str(thisYear) 
            queryString4 = "insert into lieu_days (description, days_given, given_to_user_id, given_by_user_id, year) values ('Annual leave carried from " + str(lastYear) + "', " + str(carryDays) + ", " + str(userId) + ", 1, " + str(thisYear) + ")"
            queryString5 = "update user_annual_leave set carry_processed = true where user_id = " + str(userId) + " and year = " + str(lastYear)

            query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                query.execute(queryString1 + "; " + queryString2 + "; " + queryString3 + "; " + queryString4 + "; " + queryString5)
                query.close()
            except psycopg2.Error, e:
                logger.error(e.pgerror)
                query.close()
                self.db.rollback()
                return False
        
        self.db.commit()

    def pubHolProcess(self):

        logger.debug("Entered pubHolProcess (self)")

        fromAddress = "Free-Dominion.org System <free-dominion.org@example.net>"

        query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            query.execute("select name, description, EXTRACT(YEAR from holiday_date) as year, office_id, process_event, id from public_holidays where process_event not like '';")
        except psycopg2.Error, e:
            logger.error(e.pgerror)
            query.close()
            self.db.rollback()
            return False
 
        resultset = query.fetchall()
        query.close()
               
        for row in resultset:    
            logger.debug("Entered pubHolProcess.forloop (self)")

            name = row['name']
            description = row['description']
            year = int(row['year'])
            officeId = row['office_id']
            processEvent = row['process_event']
            pubHolId = row['id']

            name.replace("'","''")
            description.replace("'","''")
 
            if processEvent == "Add":
                logger.debug("Entered pubHolProcess.processEvent=Add")
                query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
                try:
                    query.execute("update user_annual_leave set annual_leave_lieu = annual_leave_lieu + " + str(1) + ", annual_leave_remaining = annual_leave_remaining + " + str(1) + " from users,public_holidays where user_annual_leave.user_id = users.id and users.primary_office_id = " + str(officeId) + " and user_annual_leave.year = " + str(year) + " and users.join_date::timestamp < public_holidays.holiday_date::timestamp and users.leave_date::timestamp > public_holidays.holiday_date::timestamp and public_holidays.id = " + str(pubHolId) + " and countholidays(public_holidays.holiday_date,public_holidays.holiday_date,(select cast (users.week_start_day as real)),(select cast (users.week_end_day as real)),users.primary_office_id) = 0; update public_holidays set process_event = '' where id = " + str(pubHolId) + "; select users.id as userid from users,public_holidays where users.primary_office_id = " + str(officeId) + " and public_holidays.office_id = users.primary_office_id and users.join_date::timestamp < public_holidays.holiday_date::timestamp and users.leave_date::timestamp > public_holidays.holiday_date::timestamp and public_holidays.id = " + str(pubHolId) + " and countholidays(public_holidays.holiday_date,public_holidays.holiday_date,( select cast (users.week_start_day as real)),(select cast (users.week_end_day as real)),users.primary_office_id) = 0;")
                except psycopg2.Error, e:
                    logger.error(e.pgerror)
                    query.close()
                    self.db.rollback()
                    return False

                resultset = query.fetchall()
                query.close()

                for row in resultset:
                    userId = row['userid']
                    query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
                    queryString = "insert into lieu_days values ('" + name + "'," + str(1) + "," + str(userId) + "," + str(1) + "," + str(year) + "," + str(pubHolId) + ");" 
                    logger.debug(queryString)
                    try:
                        query.execute(queryString)
                        query.close()
                    except psycopg2.Error, e:
                        logger.error(e.pgerror) 
                        query.close()
                        self.db.rollback()
                        return False

            elif processEvent == "Remove":
                logger.debug("Entered pubHolProcess.processEvent=Remove")
                query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
                try:
                    query.execute("update user_annual_leave set annual_leave_lieu = annual_leave_lieu - " + str(1) + ", annual_leave_remaining = annual_leave_remaining - " + str(1) + " from users,public_holidays where user_annual_leave.user_id = users.id and users.primary_office_id = " + str(officeId) + " and user_annual_leave.year = " + str(year) + " and users.join_date::timestamp < public_holidays.holiday_date::timestamp and users.leave_date::timestamp > public_holidays.holiday_date::timestamp and public_holidays.id = " + str(pubHolId) + " and countholidays(public_holidays.holiday_date,public_holidays.holiday_date,(select cast (users.week_start_day as real)),(select cast (users.week_end_day)),users.primary_office_id) = 0; select users.id as userid from users,public_holidays where users.primary_office_id = " + str(officeId) + " and public_holidays.office_id = users.primary_office_id and users.join_date::timestamp < public_holidays.holiday_date::timestamp and users.leave_date::timestamp > public_holidays.holiday_date::timestamp and public_holidays.id = " + str(pubHolId) + " and countholidays(public_holidays.holiday_date,public_holidays.holiday_date,(select cast(users.week_start_day as real)),(select cast (users.week_end_day as real)),users.primary_office_id) = 0;")
                except psycopg2.Error, e:
                    logger.error(e.pgerror)
                    query.close()
                    self.db.rollback()
                    return False

                resultset = query.fetchall()
                query.close()

                for row in resultset:
                    userId = row['userid']
                    query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
                    queryString = "delete from lieu_days where given_to_user_id = " + str(userId) + " and year = " + str(year) + " and public_holiday_id = " + str(pubHolId) + ";"
                    logger.debug(queryString)
                    try:
                        query.execute(queryString)
                        query.close()
                    except psycopg2.Error, e:
                        logger.error(e.pgerror)
                        query.close()
                        self.db.rollback()
                        return False

                query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
                try:
                    query.execute("delete from public_holidays where id = " + str(pubHolId) + ";")
                    query.close()
                except psycopg2.Error, e:
                    logger.error(e.pgerror)
                    query.close()
                    self.db.rollback()
                    return False

        self.db.commit()

                
    def userTableChangeProcess(self):
        
        logger.debug("Entered userTableChangeProcess (self)")
        
        fromAddress = "Free-Dominion.org System <free-dominion.org@example.net>"
        
        query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            query.execute("select username, week_start_day, week_end_day, join_date, leave_date, primary_office_id, process_event, id from users where process_event not like '';")
        except psycopg2.Error, e:
            logger.error(e.pgerror)
            query.close()
            self.db.rollback()
            return False

        resultset = query.fetchall()
        query.close()
        for row in resultset:
            username = row['username']
            weekStartDay = row['week_start_day']
            weekEndDay = row['week_end_day']
            joinDate = row['join_date']
            leaveDate = row['leave_date']
            primaryOfficeId = row['primary_office_id']
            processEvent = row['process_event']
            userId = row['id']
        
            logger.info("Processing " + username + ", " + str(userId) )
            
            # NOTE: processing for all events (Add,Update etc.)

            # Add public holiday lieu days for new employment date range that are not already added
            query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
            queryString = "select distinct n1.*,n2.* from (select public_holidays.id,public_holidays.name,public_holidays.holiday_date as holiday_date,EXTRACT(YEAR from public_holidays.holiday_date) as year from public_holidays,users where public_holidays.holiday_date between '" + str(joinDate) +"' and '" + str(leaveDate) + "' and users.id=" + str(userId) + " and users.primary_office_id = public_holidays.office_id) as n1 left join (select public_holidays.id as id2 from public_holidays,lieu_days,users where users.id=" + str(userId) + " and lieu_days.given_to_user_id = users.id and lieu_days.public_holiday_id = public_holidays.id) as n2 on (n1.id=n2.id2) where (n1.id != n2.id2) or n2.id2 is null;"
            
            try:
                query.execute(queryString)
            except psycopg2.Error, e:
                logger.error(e.pgerror)
                query.close()
                self.db.rollback()
                return False
            
            resultset = query.fetchall()
            query.close()
            for row in resultset:
                logger.debug("Next add")
                pubHolId = row['id']
                pubHolName = row['name']
                pubHolDate = row['holiday_date']
                pubHolYear = int(row['year'])

                query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor) 
                queryString = "select countholidays('" + str(pubHolDate) + "','" + str(pubHolDate) + "'," + str(weekStartDay) + "," + str(weekEndDay) + ",'" + str(primaryOfficeId) + "');"
                query.execute(queryString)
                row = query.fetchone()
                query.close()
                if row['countholidays'] == 0:
                    query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor) 
                    try:
                        query.execute("insert into lieu_days values ('" + pubHolName + "'," + str(1) + "," + str(userId) + "," + str(1) + ",'" + str(pubHolYear) + "'," + str(pubHolId) + "); update user_annual_leave set annual_leave_lieu = annual_leave_lieu + " + str(1) + ", annual_leave_remaining = annual_leave_remaining + " + str(1) + " from users where user_annual_leave.user_id = users.id and user_annual_leave.year = " + str(pubHolYear) + " and users.id = " + str(userId) + ";")
                    except psycopg2.Error, e:
                        logger.error(e.pgerror)
                        query.close()
                        self.db.rollback()
                        return False
            
                    
            # Remove public holiday lieu days for new employment date range that have already been added
            query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
            queryString = "select distinct n1.*,n2.* from (select public_holidays.id,public_holidays.name,public_holidays.holiday_date as holiday_date,EXTRACT(YEAR from public_holidays.holiday_date) as year from public_holidays,users where public_holidays.holiday_date not between '" + str(joinDate) +"' and '" + str(leaveDate) + "' and users.id=" + str(userId) + " and users.primary_office_id = public_holidays.office_id) as n1 left join (select public_holidays.id as id2 from public_holidays,lieu_days,users where users.id=" + str(userId) + " and lieu_days.given_to_user_id = users.id and lieu_days.public_holiday_id = public_holidays.id) as n2 on (n1.id=n2.id2) where (n1.id = n2.id2);"
            query.execute(queryString)
            resultset = query.fetchall()
            query.close()
            for row in resultset:
                logger.debug("Next remove")
                pubHolId = row['id']
                pubHolName = row['name']
                pubHolDate = row['holiday_date']
                pubHolYear = int(row['year'])
                query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
                queryString = "select countholidays('" + str(pubHolDate) + "','" + str(pubHolDate) + "'," + str(weekStartDay) + "," + str(weekEndDay) + ",'" + str(primaryOfficeId) + "');"
                query.execute(queryString)
                row = query.fetchone()
                query.close()
                if row['countholidays'] == 1:
                    query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
                    try:
                        query.execute("delete from lieu_days where public_holiday_id = " + str(pubHolId) + " and given_to_user_id = " + str(userId) + " and year = " + str(pubHolYear) + "; update user_annual_leave set annual_leave_lieu = annual_leave_lieu - " + str(1) + ", annual_leave_remaining = annual_leave_remaining - " + str(1) + " from users where user_annual_leave.user_id = users.id and user_annual_leave.year = " + str(pubHolYear) + " and users.id = " + str(userId) + ";")
                    except psycopg2.Error, e:
                        logger.error(e.pgerror)
                        query.close()
                        self.db.rollback()
                        return False
                        
            # TODO: In case week_start_day or week_end_day has changed, check for existing public holidays lieu days from current date to leave date. Add or remove lieu days accordingly.
            
            query = self.db.cursor(cursor_factory=psycopg2.extras.DictCursor)
            query.execute("update users set process_event = '' where id = " + str(userId) + ";")
            query.close()
            self.db.commit()


    def sendMail(self,fromAddress,toAddress,subject,body,mailServer):

        msg = MIMEMultipart()
        msg['From'] = fromAddress
        msg['To'] = toAddress
        msg['Subject'] = subject
        msg.attach(MIMEText(body,'plain'))
        message = msg.as_string()
        
        try:
            # Send the mail
            server = smtplib.SMTP(mailServer, 587)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login("public", "share5")
            server.sendmail(fromAddress, toAddress, message)
            server.quit()

            logger.info("SUCCESSFULLY sent email as follows:")
            logger.info("From: " + fromAddress) 
            logger.info("To: " + toAddress)
            logger.info("Subject: " + subject)
            logger.info("Body: " + body)
            logger.info("ENDLOG")
            return True
        except SMTPException as error:
            logger.info("FAILED to sent email as follows:")
            logger.info("From: " + fromAddress) 
            logger.info("To: " + toAddress)
            logger.info("Subject: " + subject)
            logger.info("Body: " + body)
            logger.info("Error:" + error)
            logger.info("ENDLOG")
            return False

    def openDatabase(self,host,schema,username,password):
        try:
            
            self.db = psycopg2.connect(host=host, user=username, password=password, database=schema)
                
            logger.info("Connected to database!")
            return True
                
        except psycopg2.Error:
            logger.error("ERROR CONNECTING TO DATABASE!")
            
        return False
                
    def getDateString(self, date):
        if date is None:
            return ""
        else:
            return date.strftime("%d/%m/%Y")


app = App()
logger = logging.getLogger("DaemonLog")
#logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/var/log/proceventd/proceventd.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
daemon_runner = runner.DaemonRunner(app)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
