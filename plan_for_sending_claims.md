### **What is being done as I have understood?**
- Here in this backend, the openIMIS is getting the hostitals claims.
- Then these claims are being sent to the SOSYS for payment to hospital


### **To do**
- See the *CLAIMS_PAYMENT_FLOW.md*  and *.qoder/plans md* file for the detail of rep[o]
- With all the other backend system being same
- the need is to implement the call to the payement api, which i will give, send all the hospitals claims to the payemnt api that will pay to hospital
- Then the payemnt will send what has been payed
- the openimis will then track how much of the bulk payement is then sent 
- for now just igonre the aftermath of the openimis sending data to the SOSYS for validation
- Create a separate app for the hospital payment
    - where there is the api end point which shows all the claims of each hospitals collected in bulk when the cetain amount is reached(this bulk part is already implemented).
    - Then the openimis adminstrator will give permissions for the payment after watching those
    - Then after getting request, the payement api will send json of what has been paid or if all has been paid.
    - Then after getting the paid reponse to the this app, without human intervention 
    - As per the previously implemented way, send hospitals the paid detail.


### **For later**
- Sending data to the SOSYS of what has been paid.

### **Strick task to perform**
- Update the docker for removing the unrequired by commenting the extra part.
- donot forget to add the new implemented app to the main directory *openimis-be_py*