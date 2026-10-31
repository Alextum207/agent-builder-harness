from tools.crm import crm_company_lookup, crm_leads_set_score, mail_send

TOOLS = [crm_company_lookup, crm_leads_set_score, mail_send]
IRREVERSIBLE = {"mail_send"}
