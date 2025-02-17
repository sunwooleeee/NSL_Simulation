import random
from DataServer import KPIDataSaver
from SimulationEngine.ClassicDEVS.DEVSAtomicModel import DEVSAtomicModel

INF = float('inf')

 

class CustomerQueue(DEVSAtomicModel):
    
    def __init__(self, strID, globalVar):
        super().__init__(strID)

        # set Global Variables
        self.globalVar = globalVar
        self.kpi_saver = KPIDataSaver()
        self.stateList = ["WAIT", "CALL", "TRANSIT", "ANALYSIS"]
        self.state = self.stateList[0]

        # input Ports, inputs=[] 에 str 형식으로 저장 -> 이걸 어떻게 끌어올것인가> 이게 관건, 
        # 한편, Trasit 이 무엇인지 파악하는 것이 중요  
        self.addInputPort("Passenger")
        self.addInputPort("Transit")

        # output Ports
        # 각각이 의미하는 바가 무엇인지 파악하는 것이 중요 
        self.addOutputPort("Call")
        self.addOutputPort("SimumlationComplete")
        self.addOutputPort("Call_vi")
        

        # self variables
        self.addStateVariable("strID", strID)
   
        # variables
        self.passengerlst = []
        self.transitlst = []
        self.endPsgr = 0
        self.simDone = False

    def funcExternalTransition(self, strPort, objEvent):
        if strPort == "Passenger":
            self.passengerlst.append(objEvent)
            if self.state == "WAIT":
                self.state = self.stateList[1]
            else:
                self.continueTimeAdvance()
            return True
        elif strPort == "Transit":
            self.transitlst.append(objEvent)
            if self.state == "WAIT":
                self.state = self.stateList[2]
            else:
                self.continueTimeAdvance()
        else:
            print("ERROR at MainController ExternalTransition: #{}".format(self.getStateValue("strID")))
            print("inputPort: {}".format(strPort))
            print("CurrentState: {}".format(self.state))
            return False


    def funcOutput(self):
        if self.state == "CALL":
            currentPsgrId = self.passengerlst[0]
            self.addOutputEvent("Call", currentPsgrId)
            psgr = self.globalVar.getPsgrInfoByID(currentPsgrId)
            psgr.setTime("WAIT", self.getTime())
            self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} called shuttle #{} to #{}".format(self.getTime(), self.getStateValue("strID"), psgr.psgrID,psgr.psgrNum,psgr.strDepartureNode,psgr.strArrivalNode))
            self.passengerlst.pop(0)
            return True
        elif self.state == "TRANSIT":
            transitInfo = self.transitlst[0]
            if str(type(transitInfo)) != "<class 'int'>" :
                targetShuttleID = transitInfo[0]
                targetPsgr = self.globalVar.getPsgrInfoByID(int(transitInfo[1]))
                targetShuttle = self.globalVar.getShuttleInfoByID(targetShuttleID)
                if targetPsgr.strState == "WAIT":
                    targetShuttle.adjustPsgr(targetPsgr,targetPsgr.psgrNum)
                    self.globalVar.setRidePsgr(targetPsgr.psgrID)
                    targetPsgr.setPsgrShuttle(targetShuttleID)
                    targetPsgr.setTime("DEPARTURE", self.getTime())
                    targetPsgr.setState("BOARDING")
                    boardingtime = self.getTime()
                    success = True
                    shuttleID = targetShuttleID
                    dep_node = targetPsgr.strDepartureNode
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'boardingtime' : boardingtime})
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'success' : success})
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'shuttleID' : shuttleID})
                    else:
                        pass
                    self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} board {} #{} to #{}".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.psgrNum,targetShuttleID, targetPsgr.strDepartureNode,targetPsgr.strArrivalNode))
                elif targetPsgr.strState == "BOARDING":
                    targetShuttle.adjustPsgr(targetPsgr,-targetPsgr.psgrNum)
                    self.globalVar.setEndPsgr(targetPsgr.psgrID)
                    targetPsgr.setTime("ARRIVAL", self.getTime())
                    arrivaltime = self.getTime()
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'arrivaltime' : arrivaltime})
                    else:
                        pass
                    targetPsgr.setState("END")
                    self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} drop off {} #{}".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.psgrNum,targetShuttleID, targetPsgr.strArrivalNode))
                    timenow = self.getTime()
                    increased_time = (timenow - targetPsgr.departureTime) - targetPsgr.expectedArrivalTime
                    if self.globalVar.isDBsave == True:
                        self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'increased_time' : increased_time})
                    else:
                        pass
                    if targetPsgr.lastPsgr:
                        self.endPsgr = targetPsgr.psgrID
                    if self.endPsgr == self.globalVar.getCountEndPsgr():
                        self.simDone = True
            else :
                targetPsgr = self.globalVar.getPsgrInfoByID(transitInfo)
                self.globalVar.setFailPsgr(targetPsgr.psgrID)
                targetPsgr.setState("FAIL")
                self.globalVar.printTerminal("[{}][{}] Passenger #{}:{} failed boarding".format(self.getTime(), self.getStateValue("strID"), targetPsgr.psgrID,targetPsgr.psgrNum))
                dep_node = targetPsgr.strDepartureNode
                if dep_node.startswith('dynamic_'):
                    self.globalVar.remove_dynamic_node(dep_node)
                if targetPsgr.shuttle_Fail == True:
                    success = "Shuttle_Fail"
                else:
                    success = "Passenger_Fail"
                if self.globalVar.isDBsave == True:
                    self.kpi_saver.Passengers_data(self.globalVar.scenarioID, targetPsgr.psgrID, {'success' : success})
                else:
                    pass
                if targetPsgr.lastPsgr:
                    self.endPsgr = targetPsgr.psgrID
                if self.endPsgr == self.globalVar.getCountEndPsgr():
                    self.simDone = True
            self.transitlst.pop(0)
            return True
        elif self.state == "ANALYSIS":
            self.addOutputEvent("SimumlationComplete", True)
        else:
            print("ERROR at Generator OutPut: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcInternalTransition(self):
        if self.state == "CALL":
            if len(self.passengerlst) == 0:
                self.state = self.stateList[0]
            else:
                self.state = self.stateList[1]
            return True
        elif self.state == "TRANSIT":
            if self.simDone :
                self.state = self.stateList[3]
            elif len(self.transitlst) == 0:
                self.state = self.stateList[0]
            else:
                self.state = self.stateList[2]
            return True
        elif self.state == "ANALYSIS":
            self.state = self.stateList[0]
            return True
        else:
            print("ERROR at Generator InternalTransition: #{}".format(self.getStateValue("strID")))
            print("CurrentState: {}".format(self.state))
            return False

    def funcTimeAdvance(self):
        if self.state == "CALL":
            return 0
        elif self.state == "TRANSIT":
            return 0
        elif self.state == "ANALYSIS":
            return 0
        else:
            return 999999999999
