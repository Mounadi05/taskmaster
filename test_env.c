#include <stdio.h>
#include <stdlib.h>
#include <string.h>



int main() {
   printf("Hello from test env\n");
   printf("\n%s\n", getenv("myvar"));
}