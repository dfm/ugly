#!/usr/bin/env python
# -*- coding: utf-8 -*-

__all__ = ["Invitation"]

from .db import db
from sqlalchemy import Column, Integer, String, Boolean


class Invitation(db.Model):

    __tablename__ = "invitations"

    id = Column(Integer, primary_key=True)
    email = Column(String)
    sent = Column(Boolean)

    def __init__(self, email, sent=False):
        self.email = email
        self.sent = sent

    def __repr__(self):
        return "<Invitation(\"{0}\", sent={1})>".format(self.email, self.sent)
