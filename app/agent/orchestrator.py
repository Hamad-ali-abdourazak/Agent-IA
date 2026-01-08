from __future__ import annotations
from typing import Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass
import yaml

from app.agent.faq_agent import CyberFAQAgent
from app.db.database import ConversationDB


@dataclass
class AgentResponse:
    message: str
    steps: List[str] = None
    suggestions: List[Tuple[str, float]] = None
    tip: str = ""
    follow_up: str = ""
    intent: str = "general"

    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.suggestions is None:
            self.suggestions = []


class CyberOrchestrator:
    def __init__(self, kb_path: Path | None = None, db_path: Path | None = None):
        self.faq = CyberFAQAgent(kb_path=kb_path)
        self.db = ConversationDB(db_path=db_path)
        
        # Load guidance
        if kb_path is None:
            kb_path = Path(__file__).parent / "knowledge_base.yaml"
        with open(kb_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        self.guidance = data.get("guidance", {})

    def detect_intent(self, text: str) -> str:
        t = text.lower()
        t = t.replace("'", " ").replace("-", " ").replace("é", "e").replace("è", "e").replace("ê", "e")
        greeting_keywords = ["bonjour", "salut", "bonsoir", "hello", "hi", "hey", "coucou"]
        if any(k in t for k in greeting_keywords):
            return "greeting"

        intent_keywords = {
            "phishing_incident": [
                "phishing", "hameçonnage", "hameconnage", "email suspect", 
                "mail suspect", "lien suspect", "lien douteux", "ai clique", 
                "j ai clique", "clique sur", "piege", "arnaque", "scam",
                "frauduleux", "usurpation", "recu un mail", "email bizarre",
                "suspect", "douteux", "etrange"
            ],
            "password_security": [
                "mot de passe", "password", "mdp", "gestionnaire", "complexe",
                "securise", "robuste", "fort", "faible", "creer un mot",
                "changer mot", "oublie mot", "reset password", "perdu mot",
                "bloque", "verrouille", "probleme mot", "compte bloque"
            ],
            "mfa": [
                "mfa", "2fa", "authentification", "double authentification",
                "multifacteur", "code", "verification", "token", "otp",
                "deux facteurs", "validation"
            ],
            "vpn": [
                "vpn", "reseau", "a distance", "remote", "connexion",
                "distant", "tunnel", "wifi public", "reseau public",
                "travail distance", "teletravail"
            ],
            "updates": [
                "mise a jour", "maj", "patch", "correctif", "update",
                "installer", "mettre a jour", "version", "upgrade"
            ],
            "data_sensitivity": [
                "donnees sensibles", "donnees", "rgpd", "confidentiel",
                "partage", "fichier", "document", "transfert", "sensitive",
                "partager fichier", "envoyer fichier", "donnee"
            ],
            "incident_reporting": [
                "incident", "signaler", "securite", "compromis", "support",
                "alerte", "probleme", "attaque", "breach", "violation",
                "contacter", "aide", "urgence"
            ],
        }
        
        for intent, keywords in intent_keywords.items():
            if any(k in t for k in keywords):
                return intent
        
        return "general"

    def respond(self, user_text: str, session: Dict, user_id: str = "anonymous") -> AgentResponse:
        # Handle pending follow-up flows
        pending = session.get("pending_flow")
        if pending == "phishing_followup":
            return self._handle_phishing_followup(user_text, session, user_id)

        intent = self.detect_intent(user_text)
        
        # Greeting
        if intent == "greeting":
            msg = (
                "Bonjour ! Je suis CyberGuard, votre assistant en cybersécurité. "
                "Je peux vous aider avec : le phishing, les mots de passe, la MFA, "
                "le VPN, les mises à jour, la gestion des données sensibles, et le signalement d'incidents. "
                "Comment puis-je vous aider ?"
            )
            tip = self.faq.tip()
            self.db.save_conversation(user_id, user_text, msg, intent)
            self.db.increment_metric("question_asked", intent)
            suggestions = [
                ({"question": "🔐 Comment créer un mot de passe solide ?"}, 1.0),
                ({"question": "🚨 Comment détecter un email suspect ?"}, 1.0),
                ({"question": "🔑 Qu'est-ce que la MFA ?"}, 1.0)
            ]
            return AgentResponse(message=msg, steps=[], suggestions=suggestions, tip=tip, intent=intent)
        
        # Phishing incident
        if intent == "phishing_incident":
            msg = (
                "Compris. Pour un potentiel hameçonnage, restons méthodiques. "
                "Je vais vous guider étape par étape."
            )
            steps = [
                "Ne cliquez plus dans l'email et n'ouvrez pas les pièces jointes.",
                "Si vous avez entré des identifiants, changez-les immédiatement et activez la MFA.",
                "Capturez les éléments (expéditeur, sujet, lien) et signalez l'email à la sécurité.",
            ]
            suggestions = [(q.get("question", ""), s) for (q, s) in self.faq.search(user_text, top_k=3)]
            tip = self.faq.tip()
            session["pending_flow"] = "phishing_followup"
            follow_up = (
                "Avez-vous entré des identifiants ou téléchargé une pièce jointe après avoir cliqué ?"
            )
            enriched = self._enrich_md(intent)
            msg = msg + enriched
            self.db.save_conversation(user_id, user_text, msg, intent)
            self.db.increment_metric("question_asked", intent)
            return AgentResponse(message=msg, steps=steps, suggestions=suggestions, tip=tip, follow_up=follow_up, intent=intent)

        # Default: leverage FAQ + provide structured guidance
        answer, score, meta = self.faq.answer(user_text)
        suggestions = [(q.get("question", ""), s) for (q, s) in self.faq.search(user_text, top_k=3)]
        steps = self._generic_steps(intent)
        tip = self.faq.tip()

        # Clarification if too vague
        if score < 0.15 and intent in ("general", "incident_reporting"):
            msg = (
                "Je peux vous aider sur : phishing, mots de passe, MFA, VPN, mises à jour, données sensibles, "
                "signalement d'incident. Pouvez-vous préciser votre problème ?"
            )
            suggestions = [
                ({"question": "🚨 J'ai reçu un mail suspect"}, 1.0),
                ({"question": "🔐 Mon mot de passe est bloqué"}, 1.0),
                ({"question": "🔑 Activer la MFA"}, 1.0),
                ({"question": "🛡️ Signaler un incident"}, 1.0),
            ]
            self.db.save_conversation(user_id, user_text, msg, intent)
            self.db.increment_metric("question_asked", intent)
            return AgentResponse(message=msg, steps=[], suggestions=suggestions, tip=tip, intent=intent)

        # Specialized fallback for mot de passe oublié/bloqué
        if intent == "password_security" and score < 0.3:
            answer = (
                "Voyons ensemble pour votre mot de passe :\n"
                "1) Essayez la fonction « Mot de passe oublié » du portail.\n"
                "2) Si votre compte est bloqué, attendez 15 minutes puis réessayez.\n"
                "3) Si ça ne marche pas, contactez le support IT pour un reset sécurisé.\n"
                "4) Une fois réinitialisé, définissez un mot de passe unique et activez la MFA."
            )
            msg = answer + self._enrich_md("password_security")
        else:
            msg = (answer + self._enrich_md(intent)) if score >= 0.3 else (answer + self._enrich_md("general"))
        
        # Log to database
        self.db.save_conversation(user_id, user_text, msg, intent)
        self.db.increment_metric("question_asked", intent)
        
        return AgentResponse(message=msg, steps=steps, suggestions=suggestions, tip=tip, intent=intent)

    def _handle_phishing_followup(self, user_text: str, session: Dict, user_id: str) -> AgentResponse:
        t = user_text.lower()
        session.pop("pending_flow", None)

        if "oui" in t or "identifiant" in t or "mot de passe" in t:
            msg = (
                "Action immédiate requise :\n"
                "1. Changez tous vos mots de passe immédiatement\n"
                "2. Activez la MFA sur tous vos comptes\n"
                "3. Contactez l'équipe sécurité : security@company.com\n"
                "4. Surveillez vos comptes pour toute activité suspecte"
            )
            steps = [
                "Changez vos mots de passe maintenant",
                "Activez la MFA partout",
                "Contactez security@company.com",
                "Surveillez vos comptes"
            ]
        else:
            msg = (
                "Bien. Voici ce qu'il faut faire :\n"
                "1. Ne réutilisez plus cet email\n"
                "2. Signalez-le à votre équipe IT\n"
                "3. Supprimez l'email\n"
                "4. Restez vigilant pour les prochains emails"
            )
            steps = [
                "Signalez l'email à l'équipe IT",
                "Supprimez l'email sans y répondre",
                "Restez vigilant"
            ]

        tip = self.faq.tip()
        suggestions = []
        self.db.save_conversation(user_id, user_text, msg, "phishing_followup")
        return AgentResponse(message=msg, steps=steps, suggestions=suggestions, tip=tip, intent="phishing_followup")

    def _generic_steps(self, intent: str) -> List[str]:
        mapping = {
            "password_security": [
                "Utilisez un gestionnaire de mots de passe fourni par l'organisation.",
                "Créez un mot de passe d'au moins 12 caractères mélangeant majuscules, minuscules, chiffres et symboles.",
                "Activez la MFA sur tous vos comptes critiques.",
                "Ne réutilisez jamais le même mot de passe."
            ],
            "mfa": [
                "Préférez les applications d'authentification (Google Authenticator, Microsoft Authenticator) aux SMS.",
                "Gardez des codes de secours dans un coffre sécurisé.",
                "Activez la MFA sur tous les comptes qui le permettent."
            ],
            "vpn": [
                "Téléchargez le client VPN depuis le portail IT de votre organisation.",
                "Activez le VPN avant d'accéder à toute ressource interne.",
                "Utilisez toujours le VPN sur les réseaux publics ou non fiables.",
                "Fermez la session VPN après usage."
            ],
            "updates": [
                "Appliquez les patchs critiques dans les 48 heures.",
                "Installez les patchs normaux dans les 2 semaines.",
                "Redémarrez l'appareil après un patch critique.",
                "Vérifiez que la mise à jour s'est bien appliquée."
            ],
            "data_sensitivity": [
                "Utilisez uniquement les outils homologués pour partager des fichiers sensibles.",
                "Chiffrez les données en transit (HTTPS/TLS) et au repos.",
                "Limitez l'accès aux personnes vraiment autorisées.",
                "Appliquez le principe du moindre privilège."
            ],
            "incident_reporting": [
                "Collectez les éléments (logs, captures, emails) sans les altérer.",
                "Contactez immédiatement l'équipe sécurité (ne pas attendre).",
                "Créez un ticket dans le système GRC si disponible.",
                "Notifiez votre manager de la situation."
            ],
            "general": [
                "Vérifiez toujours l'expéditeur des emails.",
                "Utilisez des mots de passe robustes et uniques.",
                "Activez la MFA partout où c'est possible.",
                "En cas de doute, contactez l'équipe sécurité."
            ],
        }
        return mapping.get(intent, mapping["general"])

    def _enrich_md(self, intent: str) -> str:
        g = self.guidance.get(intent)
        if not g:
            return ""
        
        output = "\n\n**Contexte :** " + g.get("why", "")
        
        best = g.get("best_practices", [])
        if best:
            output += "\n\n**Bonnes pratiques :**\n"
            for bp in best:
                output += f"• {bp}\n"
        
        mistakes = g.get("common_mistakes", [])
        if mistakes:
            output += "\n**Erreurs courantes :**\n"
            for m in mistakes:
                output += f"⚠️ {m}\n"
        
        return output

    def get_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Return user conversation history."""
        return self.db.get_history(user_id, limit=limit)

    def get_metrics(self) -> Dict:
        """Return aggregated metrics."""
        return self.db.get_metrics()
