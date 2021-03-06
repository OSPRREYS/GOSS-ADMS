/*******************************************************************************
 * Copyright (c) 2017, Battelle Memorial Institute All rights reserved.
 * Battelle Memorial Institute (hereinafter Battelle) hereby grants permission to any person or entity
 * lawfully obtaining a copy of this software and associated documentation files (hereinafter the
 * Software) to redistribute and use the Software in source and binary forms, with or without modification.
 * Such person or entity may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 * the Software, and may permit others to do so, subject to the following conditions:
 * Redistributions of source code must retain the above copyright notice, this list of conditions and the
 * following disclaimers.
 * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and
 * the following disclaimer in the documentation and/or other materials provided with the distribution.
 * Other than as used herein, neither the name Battelle Memorial Institute or Battelle may be used in any
 * form whatsoever without the express written consent of Battelle.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL
 * BATTELLE OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
 * OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
 * GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 * General disclaimer for use with OSS licenses
 *
 * This material was prepared as an account of work sponsored by an agency of the United States Government.
 * Neither the United States Government nor the United States Department of Energy, nor Battelle, nor any
 * of their employees, nor any jurisdiction or organization that has cooperated in the development of these
 * materials, makes any warranty, express or implied, or assumes any legal liability or responsibility for
 * the accuracy, completeness, or usefulness or any information, apparatus, product, software, or process
 * disclosed, or represents that its use would not infringe privately owned rights.
 *
 * Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer,
 * or otherwise does not necessarily constitute or imply its endorsement, recommendation, or favoring by the United
 * States Government or any agency thereof, or Battelle Memorial Institute. The views and opinions of authors expressed
 * herein do not necessarily state or reflect those of the United States Government or any agency thereof.
 *
 * PACIFIC NORTHWEST NATIONAL LABORATORY operated by BATTELLE for the
 * UNITED STATES DEPARTMENT OF ENERGY under Contract DE-AC05-76RL01830
 ******************************************************************************/
package gov.pnnl.goss.gridappsd.dto;

import java.io.Serializable;

import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

public class LogMessage implements Serializable {

	private static final long serialVersionUID = 3528865632052617983L;

	public enum LogLevel {
		TRACE, DEBUG, INFO, WARN, ERROR, FATAL
	}
	public enum ProcessStatus {
		STARTING, STARTED, RUNNING, ERROR, CLOSED, COMPLETE, STOPPED, PAUSED
	}

	String source;
	String processId;
	long timestamp;
	String logMessage;
	LogLevel logLevel;
	ProcessStatus processStatus;
	Boolean storeToDb = true;
	String process_type;

	public LogMessage(){}

	public LogMessage(String source, String requestId, long timestamp, String logMessage, LogLevel logLevel, ProcessStatus processStatus, Boolean storeToDb, String process_type){
		this.source = source;
		this.processId = requestId;
		this.timestamp = timestamp;
		this.logLevel = logLevel;
		this.logMessage = logMessage;
		this.processStatus = processStatus;
		this.storeToDb = storeToDb;
		this.process_type = process_type;
	}

	public String getSource() {
		return source;
	}
	public void setSource(String source) {
		this.source = source;
	}

	public String getProcessId() {
		return processId;
	}

	public void setProcessId(String processId) {
		this.processId = processId;
	}

	public long getTimestamp() {
		return timestamp;
	}
	public void setTimestamp(long timestamp) {
		this.timestamp = timestamp;
	}
	public String getLogMessage() {
		return logMessage;
	}
	public void setLogMessage(String logMessage) {
		this.logMessage = logMessage;
	}
	public LogLevel getLogLevel() {
		return logLevel;
	}
	public void setLogLevel(LogLevel logLevel) {
		this.logLevel = logLevel;
	}
	public ProcessStatus getProcessStatus() {
		return processStatus;
	}
	public void setProcessStatus(ProcessStatus processStatus) {
		this.processStatus = processStatus;
	}
	public Boolean getStoreToDb() {
		return storeToDb;
	}
	public void setStoreToDb(Boolean storeToDb) {
		this.storeToDb = storeToDb;
	}
	
	public String getProcess_type() {
		return process_type;
	}

	public void setProcess_type(String process_type) {
		this.process_type = process_type;
	}

	public static LogMessage parse(String jsonString) throws JsonSyntaxException {
		Gson  gson = new Gson();
		LogMessage obj = gson.fromJson(jsonString, LogMessage.class);
		if(obj.logMessage==null)
			throw new JsonSyntaxException("Expected attribute logMessage not found in "+jsonString);
		return obj;
	}

	@Override
	public String toString() {
		Gson  gson = new Gson();
		return gson.toJson(this);
	}
}
