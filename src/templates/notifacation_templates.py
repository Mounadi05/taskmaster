class NotificationTemplates:
    @staticmethod
    def success_template(program_name: str, action: str) -> dict:
        """Template for successful operations"""
        return {
            'subject': f"✅ {program_name} - {action.capitalize()} Successful",
            'body': f"""
Hello,

The operation has completed successfully:

Program: {program_name}
Action: {action.capitalize()}
Status: SUCCESS
Time: {{timestamp}}

The {program_name} service has been {action}ed successfully.

Best regards,
TaskMaster System
"""
        }
    
    @staticmethod
    def failure_template(program_name: str, action: str, error_message: str) -> dict:
        """Template for failed operations"""
        return {
            'subject': f"❌ {program_name} - {action.capitalize()} Failed",
            'body': f"""
Hello,

An error occurred during the operation:

Program: {program_name}
Action: {action.capitalize()}
Status: FAILED
Error: {error_message}
Time: {{timestamp}}

Please check the system logs for more details.

Best regards,
TaskMaster System
"""
        }