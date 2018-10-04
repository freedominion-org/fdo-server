#!/usr/local/bin/python2.7

# Copyright (c) 2016 Euan Thoms <euan@potensol.com>.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


# NOTES:
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

class App():

    def __init__(self):

        self.stdin_path = '/dev/null'
        self.stdout_path = '/var/log/notifierd/stdout.log'
        self.stderr_path = '/var/log/notifierd/stderr.log'
        self.pidfile_path =  '/var/run/notifierd.pid'
        self.pidfile_timeout = 5

        self.mailServer = "smtp.example.net"

    def run(self):

        #logger.debug("Debug message")
        logger.info("Starting notifierd")
        #logger.warn("Warning message")
        #logger.error("Error message")


        dbUsername = "DB_USERNAME"
        dbPassword = "DB_PASSWORD"

        while True:
            while not self.openDatabase("pgsql.example.net","freedominion.org",dbUsername,dbPassword):
                time.sleep(30)

            while True:
                self.leaveAppNotify()
                time.sleep(30)

    def leaveAppNotify(self):

        logger.debug("Entered leaveAppNotify(self)")

        fromAddress = "Leave Application System <leave-system@example.net>"

        query = self.db.cursor()
        query.execute("select start_day,end_day,annual_leave_days,unpaid_leave_days,status,application_notes,approval_notes,date_applied,date_approval,date_modified,user_id,manager_id,email_trigger,id from annual_leave where email_trigger not like '';")

        resultset = query.fetchall()
        query.close()

        for row in resultset:

            # TODO: change query.value(x) to query.record().value("column_name")

            startDay = self.getDateString(row[0])
            endDay = self.getDateString(row[1])
            annualLeaveDays = row[2]
            unpaidLeaveDays = row[3]
            status = row[4]
            applicationNotes = row[5]
            approvalNotes = row[6]
            dateApplied = self.getDateString(row[7])
            dateApproval = self.getDateString(row[8])
            dateModified = self.getDateString(row[9])
            userId = row[10]
            managerId = row[11]
            emailTrigger = row[12]
            id = row[13]

            innerQuery = self.db.cursor()
            innerQuery.execute("select displayname, primary_email_address from users where id = " + str(userId))
            innerRow = innerQuery.fetchone()
            innerQuery.close()
            userDisplayName = innerRow[0]
            userEmailAddress = innerRow[1]
            
            innerQuery = self.db.cursor()
            innerQuery.execute("select displayname, primary_email_address from users where id = " + str(managerId))
            innerRow = innerQuery.fetchone()
            innerQuery.close()
            managerDisplayName = innerRow[0]
            managerEmailAddress = innerRow[1]

            subject = ""
            body = ""
            
            isNotifyHR = False

            logger.debug("emailTrigger: " + emailTrigger)

            if emailTrigger == "Applicant Submitted":
                subject = "Leave Application submitted by " + str(userDisplayName)
                body = "A new leave application was submitted by " + str(userDisplayName) + " on " + str(dateApplied) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."
            elif emailTrigger == "Applicant Modified":
                subject = "Leave Application modified by " + str(userDisplayName)
                body = "A leave application was modified by " + str(userDisplayName) + " on " + str(dateModified) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."
            elif emailTrigger == "Applicant Cancelled":
                subject = "Leave Application cancelled by " + str(userDisplayName)
                body = "A leave application was cancelled by " + str(userDisplayName) + ".\n\nThe leave period started on " + str(startDay) + " and ended on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."
            elif emailTrigger == "Applicant Cancellation Request":
                subject = "Leave Application cancellation request by " + str(userDisplayName)
                body = "A leave application cancellation request was submitted by " + str(userDisplayName) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."

            elif emailTrigger == "Manager Approved":
                isNotifyHR = True
                subject = "Leave Application approved by " + str(managerDisplayName)
                body = "A leave application was approved by " + str(managerDisplayName) + " on " + str(dateApproval) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."
            elif emailTrigger == "Manager Unapproved":
                subject = "Leave Application unapproved by " + str(managerDisplayName)
                body = "A leave application was unapproved by " + str(managerDisplayName) + " on " + str(dateApproval) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."
            elif emailTrigger == "Manager Tentative":
                subject = "Leave Application made tentative by " + str(managerDisplayName)
                body = "A leave application was made tentative by " + str(managerDisplayName) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."
            elif emailTrigger == "Manager Approved Cancellation":
                isNotifyHR = True
                subject = "Leave Application cancellation request approved by " + str(managerDisplayName)
                body = "A leave application cancellation request was approved by " + str(managerDisplayName) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."
            elif emailTrigger == "Manager Unapproved Cancellation":
                subject = "Leave Application cancellation request unapproved by " + str(managerDisplayName)
                body = "A leave application cancellation request was unapproved by " + str(managerDisplayName) + ".\n\nThe leave period starts on " + str(startDay) + " and ends on " + str(endDay) + ", consuming " + str(annualLeaveDays) + " annual leave days and " + str(unpaidLeaveDays) + " unpaid leave days."

            if "Applicant" in emailTrigger:
                toAddress = str(managerDisplayName) + " <" + str(managerEmailAddress)  + ">"
            elif "Manager" in emailTrigger:
                toAddress = str(userDisplayName) + " <" + str(userEmailAddress)  + ">"
            
            if subject != "":
                if self.sendMail(fromAddress,toAddress,subject,body,self.mailServer) == True:
                    innerQuery = self.db.cursor()
                    innerQuery.execute("update annual_leave set email_trigger = '' where id = " + str(id))
                    self.db.commit()
                    innerQuery.close

                if isNotifyHR:
                    body = "Leave application for " + toAddress + ":\n\n" + body
                    self.sendMail(fromAddress,"hr-dept@example.net",subject,body,self.mailServer)

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
logger.setLevel(logging.INFO)
#logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler("/var/log/notifierd/notifierd.log")
handler.setFormatter(formatter)
logger.addHandler(handler)
daemon_runner = runner.DaemonRunner(app)
daemon_runner.daemon_context.files_preserve=[handler.stream]
daemon_runner.do_action()
