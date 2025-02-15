import copy

from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel
from DataServer import KPIDataSaver
import numpy as np

INF = float('inf')

class Shuttle(DEVSAtomicModel):
    
    def __init__(self, strID, globalVar, boardingTime):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()
        self.stateList = ["IDLE", "MOVE", "BOARD"]
        self.state = self.stateList[0]

        # input Ports
        self.addInputPort("Schedule")

        # output Ports
        self.addOutputPort("Transit")
        
        # self variables
        self.addStateVariable("strID", strID)

        # variables
        self.moveTime = 0
        self.boardingTime = boardingTime
    
    def detect_position_changes(self, current_list, new_list):
        changed_items = []
        for i, item in enumerate(current_list):
            if i >= len(new_list) or item != new_list[i]:
                changed_items.append(item)
        
        changed_psgr = set(item[2] for item in changed_items)
        
        return changed_psgr
    
    
    
    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "Schedule":
            if self.getStateValue("strID") == objEvent.shuttleID:
                schedule = objEvent
                shuttle = self.globalVar.getShuttleInfoByID(schedule.shuttleID)
                psgr = self.globalVar.getPsgrInfoByID(schedule.psgrID)
                psgr.setExpectedTime(schedule.newPsgrWaitTime,schedule.newPsgrArrivalTime)
                expectedwaitingtime = schedule.newPsgrWaitTime
                expectedarrivaltime = schedule.newPsgrArrivalTime
                waitstarttime = psgr.waitingStartTime
                if self.globalVar.isDBsave == True:
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, psgr.psgrID, {"expectedwaitingtime" :expectedwaitingtime})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, psgr.psgrID, {"expectedarrivaltime" :expectedarrivaltime})
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, psgr.psgrID, {"waitstarttime" :waitstarttime})
                else:
                    pass
                self.globalVar.printTerminal("[{}][{}] recevied SCHEDULE{}".format(self.getTime(), self.getStateValue("strID"), schedule.scheduleID))
                
                changed_psgr = self.detect_position_changes(shuttle.curDst, schedule.dstLst)
                for i in changed_psgr:
                    psgr = self.globalVar.getPsgrInfoByID(i)
                    psgr.plusPath()
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, i, {'pathChanged': psgr.pathChanged})
                    else:
                        pass

                shuttle.setDstLst(schedule.dstLst)
                shuttle.setPath(schedule.totalPath)
                shuttle.setSchedule(schedule)

                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True
        else :
            print("ERROR at Generator ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False

    def funcOutput(self):
        if self.state == "MOVE":          
            shuttle = self.globalVar.getShuttleInfoByID(self.getStateValue("strID"))
            shuttle.setState("MOVE")
            graphInfo = self.globalVar.graphInfo
            if len(shuttle.curPath) > 1:
                self.moveTime = graphInfo[shuttle.curPath[0]]['links'][shuttle.curPath[1]]['time']
                current_node = shuttle.curPath[0]
                if shuttle.curNode == shuttle.curDst[0][0]:  
                    self.globalVar.printTerminal("[{}][{}] arrived #{} for #{} ".format(self.getTime(), self.getStateValue("strID"), shuttle.curNode, shuttle.curDst[0][1]))
                else :
                    self.globalVar.printTerminal("[{}][{}] moved from #{} to #{} [Next Stop : #{}]".format(self.getTime(), self.getStateValue("strID"), shuttle.curPath[0], shuttle.curPath[1],shuttle.curDst[0][0]))
                    if current_node.startswith('dynamic_'):
                        # 동적 노드 삭제
                        self.globalVar.remove_dynamic_node(current_node)
            
            shuttle.setActivationTime(shuttle.schedule.scheduleID, self.moveTime)
            shuttle.setPsgrLoad(shuttle.curPsgrNum, self.moveTime)
            shuttle.shuttleID = self.getStateValue("strID")
            # print(shuttle.curDst)
            # vi_shuttle = {}
            # vi_shuttle['shuttle_id'] = self.getStateValue("strID")
            # vi_shuttle['curNode'] = shuttle.curNode
            # vi_shuttle['curPath'] = shuttle.curPath
            # vi_shuttle['curDst'] = shuttle.curDst
            # vi_shuttle['curPsgr'] = shuttle.curPsgr
            
            if self.globalVar.isDBsave == True:
                currenttime = self.getTime()
                state = shuttle.strState
                curNode = shuttle.curNode
                curPath = shuttle.curPath
                curDst = shuttle.curDst
                curPsgr = [passenger.psgrID for passenger in shuttle.curPsgr]
                curPsgrNum = shuttle.curPsgrNum
                self.kpi_saver.vehicle_data(self.globalVar.scenarioID, currenttime, shuttle.shuttleID, state, curDst, curNode, curPath, curPsgr, curPsgrNum)
            else:
                pass
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, currenttime)
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, state), 
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID. curDst),
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, curNode)
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID, curPath)
            # dbfunction (self.globalVar.scenarioID, shuttle.shuttleID. curPsgr)
            
            # self.addOutputEvent("CurPath", vi_shuttle)
            return True
        elif self.state == "BOARD":
            shuttle = self.globalVar.getShuttleInfoByID(self.getStateValue("strID"))
            shuttle.setState("BOARD")
            if shuttle.curDst[0][1] == "BOARDING":
                self.globalVar.printTerminal("[{}][{}] boarded passengers at #{} ".format(self.getTime(), self.getStateValue("strID"), shuttle.curNode))
            else:
                self.globalVar.printTerminal("[{}][{}] dropped off passengers at #{} ".format(self.getTime(), self.getStateValue("strID"), shuttle.curNode))
            dstPsgr = shuttle.curDst[0][2]
            self.addOutputEvent("Transit", [self.getStateValue("strID"), dstPsgr])
            shuttle.delDst()
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        shuttle = self.globalVar.getShuttleInfoByID(self.getStateValue("strID"))
        if self.state == "MOVE":
            if shuttle.curNode == shuttle.curDst[0][0]:
                 self.state = self.stateList[2]
            elif len(shuttle.curPath) > 1:
                self.state = self.stateList[1]
                shuttle.setPath(shuttle.curPath[1:])
                shuttle.setNode(shuttle.curPath[0])
                shuttle.setCoordinates(self.globalVar.getNodeInfoByID(shuttle.curPath[0]))
        elif self.state == "BOARD":
            if len(shuttle.curPath) > 1:
                if shuttle.curNode == shuttle.curDst[0][0]: 
                    self.state = self.stateList[2]
                else :
                    self.state = self.stateList[1]
            else:
                shuttle.setState("WAIT")
                shuttle.setPath([])
                self.state = self.stateList[0]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "MOVE":
            return self.moveTime
        elif self.state == "BOARD":
            return self.boardingTime
        else:
            return 999999999999

