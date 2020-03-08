/*
 * ========================================= README =============================================
 * This script can be used to create a simple serial communication between an Arduino and an other
 * machine.
 * =================================================================
 * Change the constant to make this script working for your own project.
 * 
 * BAUD_RATE constant is the baud rate used for the serial communication.
 * 
 * BUFFER_SIZE is the maximum size of the software buffer used for reception.
 * 
 * SEND_BUFFER_SIZE is the maximum size of the software buffer used for sending messages.
 * 
 * MAX_RECEIVING_DELAY is the maximum delay the program will wait after detetecting a new message.
 * If the message end is not detected after this delay, the receiving buffer will be cleared.
 * 
 * WATCHDOG_DELAY constant can takes folowing values :
 * 
 *   time before watchdog firing    argument of wdt_enable()
 * -------------------------------------------------------
 * 15mS                           WDTO_15MS
 * 30mS                           WDTO_30MS
 * 60mS                           WDTO_60MS
 * 120mS                          WDTO_120MS
 * 250mS                          WDTO_250MS
 * 500mS                          WDTO_500MS
 * 1S                             WDTO_1S            
 * 2S                             WDTO_2S
 * 4S                             WDTO_4S
 * 8S                             WDTO_8S
 * 
 * The chosen value is used as maximum time for an execution of the loop function. If the loop
 * takes too long to execute then the Arduino will reset itself.
 * =================================================================
 * The messages used to communicate with the Arduino MUST start with 3 * 255 bytes and end with
 * 3 * 254 bytes. It also needs to have a message id cntained in the 4th byte.
 * Ex : 255 255 255 1 ... 254 254 254 (The message id is 1).
 * 
 * If you want to send a message with the Arduino you MUST "give" a token to the Arduino to
 * tell it it can use the serial canal. To give a token to the Arduino you MUST use the function
 * set_token that will allow the program to destroy the token after sending a message or after
 * token's life span is over. The set_token function takes an unsigned int as parameter that tell 
 * the function how long the token will last (in ms). You can use the get_token_life_span function
 * to read the 5th and 6th bytes of the message and convert it in a value to use as life span.
 * Ex : 255 255 255 1 0 200 ... 254 254 254 (Message id = 1, life span = 200).
 * 
 * You can write the behaviour you want for the Arduino for each message id in the function 
 * message_handler. Just add a case to the switch case for the id you want to use. Don't forget
 * to add a comment your new case to not forget what it is used for! :)
 * 
 * If you find a bug please contact us.
 * ================================================================================================
 */

#include <avr/wdt.h>


// CONST
# define BAUD_RATE 115200
# define BUFFER_SIZE 255
# define SEND_BUFFER_SIZE 255
# define MAX_RECEIVING_DELAY 1000
# define WATCHDOG_DELAY WDTO_500MS

# define DEBUG_LED_0 A0
# define DEBUG_LED_1 A1
# define DEBUG_LED_2 A2

// Global variables
unsigned char serial_buffer[BUFFER_SIZE];
unsigned int top_buffer = 0;

unsigned char send_buffer[SEND_BUFFER_SIZE];
unsigned int top_send_buffer = 0;

unsigned char message_id = 0;
unsigned char message[BUFFER_SIZE - 7];
unsigned int top_message = 0;
unsigned long time_start_rcv = 0;

bool has_token = false;
unsigned long time_token = 0;
unsigned int token_life_span = 0;


bool new_message = false; 


// SERIAL COMMUNICATION FUNCTIONS

void read_buffer();
void clear_buffer();
void add_to_buffer(char char_to_add);
void check_buffer();
void read_message();
bool send_message();
void clear_send_buffer();
void message_handler();
void token_manager();
void set_token(unsigned int life_span);
unsigned int get_token_life_span();


//OTHERS FUNCTIONS

void refresh_wdt(int wdt_delay);

// DEBUG FUNCTIONS

void write_buffer();
void pong(char toSend);
void ledDebug1();
void ledDebug2();
void ledDebug3();
void sendDebug();

/*================================ ROUTINE ====================================*/
void setup() {
  Serial.begin(BAUD_RATE);

  // DEBUG
  //Serial.write("RESTART\n");
  
  pinMode(DEBUG_LED_0, OUTPUT);
  pinMode(DEBUG_LED_1, OUTPUT);
  pinMode(DEBUG_LED_2, OUTPUT);

  digitalWrite(DEBUG_LED_0, HIGH);
  delay(1000);
  digitalWrite(DEBUG_LED_0, LOW);
  
  /*
  String message = "coucou";
  for(int i = 0; i < 6; i++){
      add_to_buffer(message[i]);
   }
  */
}

void loop() {
  // DEBUG



  //===============================
  refresh_wdt(WATCHDOG_DELAY); // Write here the maximum time for a loop.
  read_buffer(); // If there are bytes in the buffer, put the first one in the serial_buffer variable.
  check_buffer(); // Manage the reception of the messages.
  read_message(); // Stores the message information in message_id and message.
  message_handler(); // If a new message is receive do the job according to the message id.
  token_manager(); // Destroy communication token if times out to avoid serial communication collisions. 
  //===============================

  // DEBUG
    
  //ledDebug3();
  //write_buffer();

}

/*================================ SERIAL COMMUNICATION FUNCTIONS ====================================*/


void read_buffer(){
  // If there are bytes in Arduino's buffer, then we stores the first one in the serial_buffer variable.
  if(Serial.available()){
    add_to_buffer(Serial.read());
  }
  
}


void clear_buffer(){
  // Clear the buffer by setting the top_buffer variable to 0.
  top_buffer = 0;   
}


void add_to_buffer(char char_to_add){
  // Add a given char to the buffer. It contains a condition to avoid overflow. If buffer is full then it clear the buffer and stores
  // the char in the empty buffer.
  if(top_buffer < BUFFER_SIZE){
    serial_buffer[top_buffer] = char_to_add;
    top_buffer += 1;
    ledDebug1(); //DEBUG
  }
  else{
    clear_buffer();
    add_to_buffer(char_to_add);
    digitalWrite(DEBUG_LED_2, HIGH); //DEBUG
  }    
}

void check_buffer(){
  // Manage the reception of the messages
  if(time_start_rcv != 0){
    if(millis() - time_start_rcv > MAX_RECEIVING_DELAY){
      clear_buffer();
      time_start_rcv = 0;
      digitalWrite(DEBUG_LED_0, LOW); // DEBUG
    }
  }
  // Start message detection
  if (top_buffer == 3){
    if(serial_buffer[0] != 255 ||  serial_buffer[1] != 255 || serial_buffer[2] != 255){
      serial_buffer[0] = serial_buffer[1];
      serial_buffer[1] = serial_buffer[2];
      top_buffer = 2;
    }
    else{
      time_start_rcv = millis();
      digitalWrite(DEBUG_LED_0, HIGH); // DEBUG
    }
  }
  // Stop message detection
  else if (top_buffer >= 6){
    if(serial_buffer[top_buffer - 3] == 254 &&  serial_buffer[top_buffer - 2] == 254 && serial_buffer[top_buffer - 1] == 254){
      new_message = true;    
    }
  }
}


void read_message(){
  // Read the message, stores its id in message_id and its content in message. Its length is stored in top_message. 
  if(new_message == true){
    message_id = serial_buffer[3];
    for (int i = 4; i < top_buffer - 3; i++){
      message[i - 4] = serial_buffer[i];
    }
    top_message = top_buffer - 7;
    new_message = false;
    clear_buffer();
    }
}


bool send_message(){
  // Send the message if the arduino has the communication token.
  token_manager();
  if(has_token){
    for (int i = 0; i < top_send_buffer; i++){
      Serial.write(send_buffer[i]);     
    }
    clear_send_buffer();
    has_token = false;
    return true;
  }
  else{
    clear_send_buffer();
    return false;
  }
}

void clear_send_buffer(){
  // Clear the send buffer
  top_send_buffer = 0;
}


void message_handler(){
  //============================
  // Write new behaviour there !!
  //============================
  switch (message_id){
    case 1:
    // Receive new positions
    break;
    case 2:
    // Ask motor data
    set_token(get_token_life_span());
    sendDebug(); // DEBUG
    digitalWrite(DEBUG_LED_1, HIGH);
    break;
    case 3:
    // Receive new torques
    break;
    case 4:
    // Ask motor extinction
    break;
    case 5:
    // Ask motor control
    break;
    default:
    break;
  }
  message_id = 0; // Have to be done to avoid repetition of the task.
}


void token_manager(){
  // Destroy the token if times out.
  if(has_token){
    if(millis() - time_token > token_life_span){
      has_token = false;
    }
  }
}


void set_token(unsigned int life_span){
  // Set has_token to true et time_token to the actual millis() value.
  if(life_span > 0){
    has_token = true;
    token_life_span = life_span;
    time_token = millis();
  }
}


unsigned int get_token_life_span(){
  // Read 2 first bytes of an incoming message and convert it into an unsigned int to use as token life span.
  if(top_message >= 2){
    unsigned int life_span = message[0] * 256 + message[1];
    return life_span;
  }
  else{
    unsigned int life_span = 0;
    return life_span;  
  }
}


/*================================ OTHERS FUNCTIONS ====================================*/


void refresh_wdt(int wdt_delay){
  // Reset the watchdog with given delay
  /*
  time before watchdog firing    argument of wdt_enable()
-------------------------------------------------------
15mS                           WDTO_15MS
30mS                           WDTO_30MS
60mS                           WDTO_60MS
120mS                          WDTO_120MS
250mS                          WDTO_250MS
500mS                          WDTO_500MS
1S                             WDTO_1S            
2S                             WDTO_2S
4S                             WDTO_4S
8S                             WDTO_8S
  */
  wdt_enable(wdt_delay);
}




/*================================ DEBUG FUNCTIONS ====================================*/
void write_buffer(){
  for(int i = 0; i < top_buffer; i++){
    Serial.write(serial_buffer[i]);
  }
  Serial.write("\n");
}

void pong(char toSend){
  Serial.write(toSend);
}

void ledDebug1(){
  if (serial_buffer[top_buffer - 1] == '0'){
    digitalWrite(DEBUG_LED_1, HIGH);
  }
  else{
    digitalWrite(DEBUG_LED_1, LOW);
  }
  
}

void ledDebug2(){
  if (top_message != 0){
    digitalWrite(DEBUG_LED_2, HIGH);
  }
  else{
    digitalWrite(DEBUG_LED_2, LOW);
  }  
}

void ledDebug3(){
  if (has_token){
    digitalWrite(DEBUG_LED_2, HIGH);
  }
  else{
    digitalWrite(DEBUG_LED_2, LOW);
  }  
}

void sendDebug(){
  send_buffer[0] = 255;
  send_buffer[1] = 255;
  send_buffer[2] = 255;
  send_buffer[3] = 1;
  send_buffer[4] = 0;
  send_buffer[5] = 254;
  send_buffer[6] = 254;
  send_buffer[7] = 254;
  top_send_buffer = 8;
  send_message();
}
