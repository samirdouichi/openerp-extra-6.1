# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import datetime
import re

from osv import fields
from osv import osv
from tools.translate import _


class dm_campaign_type(osv.osv): #{{{
    _name = "dm.campaign.type"
    _columns = {
        'name': fields.char('Description', size=64, translate=True,
                                                                 required=True),
        'code': fields.char('Code', size=16, translate=True, required=True),
        'description': fields.text('Description', translate=True),
    }

dm_campaign_type()#}}}


class account_analytic_account(osv.osv): # {{{
    _inherit = 'account.analytic.account'
    _columns = {
        'code': fields.char('Code', size=64),
    }

account_analytic_account() # }}}


class dm_campaign(osv.osv): #{{{
    _name = "dm.campaign"
    _inherits = {'account.analytic.account': 'analytic_account_id'}
    _rec_name = 'name'

    def dtp_making_time_get(self, cr, uid, ids, name, arg, context={}):
        result = {}
        for i in ids:
            result[i] = 0.0
        return result

    def onchange_lang_currency(self, cr, uid, ids, country_id):
        value = {}
        if country_id:
            country = self.pool.get('res.country').browse(cr, uid, [country_id])[0]
            value['lang_id'] = country.main_language.id
            value['currency_id'] = country.main_currency.id
            value['forwarding_charge'] = country.forwarding_charge
        else:
            value['lang_id'] = 0
            value['currency_id'] = 0
            value['forwarding_charge'] = 0.0
        return {'value': value}

    def _quantity_planned_total(self, cr, uid, ids, name, args, context={}):
        result = {}
        campaigns = self.browse(cr, uid, ids)
        for campaign in campaigns:
            quantity = 0
            for propo in campaign.proposition_ids:
                if propo.quantity_planned:
                    quantity += propo.quantity_planned
            result[campaign.id] = str(quantity)
        return result

    def _quantity_wanted_total(self, cr, uid, ids, name, args, context={}):
        result = {}
        campaigns = self.browse(cr, uid, ids)
        for campaign in campaigns:
            quantity = 0
            numeric = True
            for propo in campaign.proposition_ids:
                if propo.quantity_wanted.isdigit():
                    quantity += int(propo.quantity_wanted)
                elif propo.quantity_wanted == "AAA for a Segment":
                    result[campaign.id] = 'AAA for a Segment'
                    numeric = False
                    break
                else:
                    result[campaign.id] = 'Check Segments'
                    numeric = False
                    break
            if numeric:
                result[campaign.id] = str(quantity)
        return result

    def _quantity_delivered_total(self, cr, uid, ids, name, args, context={}):
        result = {}
        campaigns = self.browse(cr, uid, ids)
        for campaign in campaigns:
            quantity = 0
            numeric = True
            for propo in campaign.proposition_ids:
                if propo.quantity_delivered.isdigit():
                    quantity += int(propo.quantity_delivered)
                else:
                    result[campaign.id] = 'Check Segments'
                    numeric = False
                    break
            if numeric:
                result[campaign.id] = str(quantity)
        return result

    def _quantity_usable_total(self, cr, uid, ids, name, args, context={}):
        result = {}
        campaigns = self.browse(cr, uid, ids)
        for campaign in campaigns:
            quantity = 0
            numeric = True
            for propo in campaign.proposition_ids:
                if propo.quantity_usable.isdigit():
                    quantity += int(propo.quantity_usable)
                else:
                    result[campaign.id] = 'Check Segments'
                    numeric = False
                    break
            if numeric:
                result[campaign.id] = str(quantity)
        return result

    def _quantity_real_total(self, cr, uid, ids, name, args, context={}):
        result = {}
        campaigns = self.browse(cr, uid, ids)
        for campaign in campaigns:
            quantity = 0
            numeric = True
            for propo in campaign.proposition_ids:
                if propo.quantity_real.isdigit():
                    quantity += int(propo.quantity_real)
                else:
                    result[campaign.id] = 'Check Segments'
                    numeric = False
                    break
            if numeric:
                result[campaign.id] = str(quantity)
        return result

    _columns = {
        'offer_id': fields.many2one('dm.offer', 'Offer',
                                    domain=[('state', 'in', ['ready', 'open']),
                                ('type', 'in', ['new', 'standart', 'rewrite'])],
                                required=True,
                                help="Choose the commercial offer to use with this campaign, only offers in ready to plan or open state can be assigned"),
        'country_id': fields.many2one('res.country', 'Country', required=True,
                                      help="The language and currency will be automaticaly assigned if they are defined for the country"),
        'lang_id': fields.many2one('res.lang', 'Language'),
        'trademark_id': fields.many2one('dm.trademark', 'Trademark'),
        'notes': fields.text('Notes'),
        'proposition_ids': fields.one2many('dm.campaign.proposition', 'camp_id',
                                            'Proposition'),
        'campaign_type_id': fields.many2one('dm.campaign.type', 'Type'),
        'analytic_account_id': fields.many2one('account.analytic.account',
                                               'Analytic Account',
                                               ondelete='cascade'),
        'planning_state': fields.selection([('pending', 'Pending'),
                                            ('inprogress', 'In Progress'),
                                            ('done', 'Done')],
                                            'Planning Status',
                                            readonly=True),
        'translation_state': fields.selection([('pending', 'Pending'),
                                               ('inprogress', 'In Progress'),
                                               ('done', 'Done')],
                                               'Translation Status',
                                               readonly=True),
        'dealer_id': fields.many2one('res.partner', 'Dealer',
                                     domain=[('category_id', 'ilike', 'Dealer')],
                                     context={'category_xml_id': 'cat_dealer'},
                                     help="The dealer is the partner the campaign is planned for."),
        'responsible_id': fields.many2one('res.users', 'Responsible'),
#        'invoiced_partner_id': fields.many2one('res.partner',
#                                                'Invoiced Partner'),
#        'files_delivery_address_id': fields.many2one('res.partner.address',
#                                                         'Delivery Address'),
        'dtp_making_time': fields.function(dtp_making_time_get,
                                            method=True, type='float',
                                             string='Making Time'),
        'deduplicator_id': fields.many2one('res.partner', 'Deduplicator',
                            domain=[('category_id', 'ilike', 'Deduplicator')],
                            context={'category_xml_id': 'cat_deduplicator'},
                            help="The deduplicator is a partner responsible to remove identical addresses from the customers list"),
        'cleaner_id': fields.many2one('res.partner', 'Cleaner',
                                 domain=[('category_id', 'ilike', 'Cleaner')],
                                 context={'category_xml_id': 'cat_cleaner'},
                                 help="The cleaner is a partner responsible to remove bad addresses from the customers list"),
        'currency_id': fields.many2one('res.currency', 'Currency',
                                                        ondelete='cascade'),
        'manufacturing_cost_ids': fields.one2many('dm.campaign.manufacturing_cost',
                                                   'campaign_id',
                                                   'Manufacturing Costs'),
        'manufacturing_product_id': fields.many2one('product.product',
                                                    'Manufacturing Product'),
        'router_id': fields.many2one('res.partner', 'Router',
                                    domain=[('category_id', 'ilike', 'Router')],
                                    context={'category_xml_id': 'cat_router'},
            help="The router is the partner who will send the mailing to the final customer"),
        'quantity_planned_total': fields.function(_quantity_planned_total,
                                    string='Total planned Quantity' ,type="char",
                                     size=64, method=True, readonly=True),
        'quantity_wanted_total': fields.function(_quantity_wanted_total,
                                        string='Total Wanted Quantity',
                                        type="char", size=64, method=True,
                                        readonly=True),
        'quantity_delivered_total': fields.function(_quantity_delivered_total,
                                            string='Total Delivered Quantity',
                                            type="char", size=64, method=True,
                                            readonly=True),
        'quantity_usable_total': fields.function(_quantity_usable_total,
                                             string='Total Usable Quantity',
                                             type="char", size=64, method=True,
                                             readonly=True),
        'quantity_real_total': fields.function(_quantity_real_total,
                                             string='Total Real Quantity',
                                             type="char", size=64, method=True,
                                             readonly=True),
        'forwarding_charge': fields.float('Forwarding Charge', digits=(16, 2)),
        'journal_id': fields.many2one('account.journal', 'Payment Methods', domain="[('type','=','cash')]"),
        'mail_service_ids': fields.one2many('dm.campaign.mail_service',
                                            'campaign_id', 'Mailing Service'),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'translation_state': lambda *a: 'pending',
        'responsible_id': lambda obj, cr, uid, context: uid,
    }

    def state_draft_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def state_close_set(self, cr, uid, ids, *args):
        for camp in self.browse(cr, uid, ids):
            if (camp.date > time.strftime('%Y-%m-%d')):
                raise osv.except_osv("Error", "Campaign cannot be closed before end date")
        self.write(cr, uid, ids, {'state': 'close'})
        return True

    def check_forbidden_country(self, cr, uid, offer_id, country):
        offers = self.pool.get('dm.offer').browse(cr, uid, offer_id)
        forbidden_state_ids = [state_id.country_id.id for state_id in
                                offers.forbidden_state_ids]
        forbidden_country_ids = [country_id.id for country_id in
                                 offers.forbidden_country_ids]
        forbidden_country_ids.extend(forbidden_state_ids)
        if country  in  forbidden_country_ids:
            return False
        return True

    def state_pending_set(self, cr, uid, ids, *args):
        self.write(cr, uid, ids, {'state': 'pending'})
        return True

    def state_open_set(self, cr, uid, ids, *args):
        camp = self.browse(cr, uid, ids)[0]
        if not camp.date_start or not \
                camp.dealer_id or not \
                camp.trademark_id or not \
                camp.lang_id or not \
                camp.currency_id:
            raise osv.except_osv("Error", "Informations are missing.Check Drop Date, Dealer, Trademark, Language and Currency")

        if (camp.date_start > time.strftime('%Y-%m-%d')):
            raise osv.except_osv("Error!!", "Campaign cannot be opened before drop date")

        # Create Flow Start Workitems
        start_type_ids = self.pool.get('dm.offer.step.type').search(cr, uid,
                                                    [('flow_start', '=', True)])
        step_ids = self.pool.get('dm.offer.step').search(cr, uid,
                                        [('offer_id', '=', camp.offer_id.id),
                                         ('type_id', 'in', start_type_ids)])
        for step in step_ids:
            for propo in camp.proposition_ids:
                for seg in propo.segment_ids:
                    if seg.type_src == 'internal' and seg.customers_file_id:
                        res = self.pool.get('dm.workitem').create(cr, uid,
                            {'segment_id': seg.id,
                             'step_id': step,
                            'source': seg.customers_file_id.source,
                            'is_global': True,
                            'action_time': time.strftime("%Y-%m-%d %H:%M:%S")})

        # Check for mail service for each offer step of a campaign
        for step in camp.offer_id.step_ids:
            mail_service = self.pool.get('dm.campaign.mail_service').search(cr,
                                        uid, [('offer_step_id', '=', step.id)])
            if not mail_service:
                raise osv.except_osv(_('Could not open this Campaign'), _('Assign a Mail Service for "%s".' % step.name))

        self.write(cr, uid, ids, {'state': 'open',
                                  'planning_state': 'inprogress'})

        # create offer history

        history_vals = {
              'offer_id': camp.offer_id.id,
              'date': camp.date_start,
              'campaign_id': camp.id,
              'code': camp.code,
              'responsible_id': camp.responsible_id.id,
              }
        history = self.pool.get("dm.offer.history")
        history.create(cr, uid, history_vals, {})
        return True

    def write(self, cr, uid, ids, vals, context=None):
        camp = self.pool.get('dm.campaign').browse(cr, uid, ids)[0]
        offer_id = 'offer_id' in vals and vals['offer_id'] or camp.offer_id.id
        country_id = 'country_id' in vals and vals['country_id'] or camp.country_id.id

        if not self.check_forbidden_country(cr, uid, offer_id, country_id):
            raise osv.except_osv("Error", "You cannot use this offer in this country")

        # In campaign, if no forwarding_charge is given,
        # it gets the 'forwarding_charge' from country
#        if not camp.forwarding_charge:
#            if camp.country_id.forwarding_charge:
#                vals['forwarding_charge'] = camp.country_id.forwarding_charge

        if camp.country_id.journal_id:
            journal_id = camp.country_id.journal_id[0].id
            vals['journal_id'] = journal_id

        #Set campaign end date at one year after start date if end date does not exist

        if 'date_start' in vals and vals['date_start']:
            d = time.strptime(vals['date_start'], "%Y-%m-%d")
            d = datetime.datetime(d[0], d[1], d[2])
            date_end = d + datetime.timedelta(days=365)
            vals['date'] = date_end.strftime('%Y-%m-%d')

            if not 'forwarding_charge' in vals:
                vals['forwarding_charge'] = 0.0

            # Set dates for propositions and segments of the campaign
            for propo in camp.proposition_ids:
                self.pool.get('dm.campaign.proposition').write(cr, uid, [propo.id],
                        {'date_start': vals['date_start'], 'date':vals['date'],
                            'forwarding_charge':vals['forwarding_charge']})
                for seg in propo.segment_ids:
                    self.pool.get('dm.campaign.proposition.segment').write(cr,
                            uid, [seg.id], {'date_start':vals['date_start'],
                            'date':vals['date']})

            #  moved in dm_retro_planning as project_id moved in retro_planning
            #if 'project_id' in vals and vals['project_id']:
                #self.pool.get('project.project').write(cr, uid,
                 #                               [vals['project_id']],
                 #                           {'date_end': vals['date_start']})

        # In campaign, if no trademark is given, it gets the 'recommended trademark' from offer
        """
        if (not camp.trademark_id) and camp.offer_id.recommended_trademark_id:
            vals['trademark_id'] = camp.offer_id.recommended_trademark_id.id
        """

        if 'trademark_id' in vals and vals['trademark_id']:
            trademark_id = vals['trademark_id']
        else:
            trademark_id = camp.trademark_id.id
        if 'dealer_id' in vals and vals['dealer_id']:
            dealer_id = vals['dealer_id']
        else:
            dealer_id = camp.dealer_id.id
        if 'country_id' in vals and vals['country_id']:
            country_id = vals['country_id']
        else:
            country_id = camp.country_id.id

        return super(dm_campaign, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context={}):
        type_id = self.pool.get('dm.campaign.type').search(cr, uid, [('code', '=', 'model')])[0]
        if 'campaign_type' in context and context['campaign_type'] == 'model':
            vals['campaign_type_id'] = type_id
        id_camp = super(dm_campaign, self).create(cr, uid, vals, context)
        data_cam = self.browse(cr, uid, id_camp)
        if not self.check_forbidden_country(cr, uid, data_cam.offer_id.id,
                                            data_cam.country_id.id):
            raise osv.except_osv("Error", "You cannot use this offer in this country")
        # create campaign mail service:
#        mail_service_id = for each step in the offer the system should:
#            - check the media of the step,
#            - find the default mail service for that media
#            - assign it to mail_service_id
#        action_id = the action_id of the mail service
        mail_service_obj = self.pool.get('dm.mail_service')
        for step_id in data_cam.offer_id.step_ids:
            mail_service_id = mail_service_obj.search(cr, uid,
                                        [('media_id', '=', step_id.media_id.id),
                                          ('default_for_media', '=', True)])
            mail_service = mail_service_obj.browse(cr, uid, mail_service_id)
            for mail in mail_service:
                mail_vals = {
                    'campaign_id': id_camp,
                    'offer_step_id': step_id.id,
                    'mail_service_id': mail.id,
#                   'action_id': mail_service.action_id.id
                }
                self.pool.get('dm.campaign.mail_service').create(cr, uid,
                                                                 mail_vals)
        # In campaign, if no forwarding_charge is given, it gets the
        #'forwarding_charge' from offer
        write_vals = {}
#        if not data_cam.forwarding_charge:
#            if data_cam.country_id.forwarding_charge:
#                write_vals['forwarding_charge'] =
#                                          data_cam.country_id.forwarding_charge

        if data_cam.country_id.journal_id:
            journal_id = data_cam.country_id.journal_id[0].id
            write_vals['journal_id'] = journal_id

        # Set campaign end date at one year after start date if end date does
        #                                                            not exist
        if (data_cam.date_start) and (not data_cam.date):
            d = time.strptime(data_cam.date_start, "%Y-%m-%d")
            d = datetime.datetime(d[0], d[1], d[2])
            date_end = d + datetime.timedelta(days=365)
            write_vals['date'] = date_end.strftime('%Y-%m-%d')

        # Set trademark to offer's trademark only if trademark is null
        """
        if vals['campaign_type_id'] != type_id:
            if vals['offer_id'] and (not vals['trademark_id']):
                offer_id = self.pool.get('dm.offer').browse(cr, uid,
                                                            vals['offer_id'])
                write_vals['trademark_id'] = offer_id.recommended_trademark_id.id
        """
        if write_vals:
            super(dm_campaign, self).write(cr, uid, id_camp, write_vals)

        return id_camp

    def fields_view_get(self, cr, user, view_id=None, view_type='form',
                context=None, toolbar=False,): # submenu=False): for trunk client
        result = super(dm_campaign, self).fields_view_get(cr, user,
            view_id, view_type, context, toolbar,) # submenu=submenu) for trunk client
        if 'campaign_type' in context:
            if context['campaign_type'] == 'model':
                if 'toolbar' in result:
                    result['toolbar']['action'] = []
        return result

    def copy_campaign(self, cr, uid, ids, *args):
        camp = self.browse(cr, uid, ids)[0]
        default = {}
        default['name'] = 'New campaign from model %s' % camp.name
        default['campaign_type_id'] = self.pool.get('dm.campaign.type').search(cr,
                                        uid, [('code', '=', 'recruiting')])[0]
        default['responsible_id'] = uid
        context = {'camp_from_model':True}
        self.copy(cr, uid, ids[0], default, context)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if not context:
            context = {}
        if not default:
            default = {}
        campaign_id = self.browse(cr, uid, id)
        if not default.get('name', False):
            default['name'] = campaign_id.name + ' (Copy)'
            # project_id should nt b her moved in rp
#        default.update({'date_start': False, 'date': False})
        default.update({
#                        'date_start': False,
#                        'date': False,
                        'proposition_ids': []})
        print "XXX default :", default
        print "XXX context :", context
        camp_copy_id = super(dm_campaign, self).copy(cr, uid, id, default, context)
#        prop_ids = [x.id for x in campaign_id.proposition_ids]
#        for proposition in campaign_id.proposition_ids:
#            default = {'camp_id': camp_copy_id}
#            prop_copy = self.pool.get('dm.campaign.proposition').copy(cr,
#                   uid, proposition.id, default, context)
        return camp_copy_id

    def unlink(self, cr, uid, ids, context={}):
        for campaign in self.browse(cr, uid, ids, context):
            history_id = self.pool.get('dm.offer.history').search(cr,
                            uid, [('campaign_id', '=', campaign.id)])
            self.pool.get('dm.offer.history').unlink(cr, uid, history_id,
                                                                     context)
        return super(dm_campaign, self).unlink(cr, uid, ids, context)

dm_campaign()#}}}


class dm_offer_history(osv.osv): # {{{
    _inherit = "dm.offer.history"
    _columns = {
        'campaign_id': fields.many2one('dm.campaign', 'Name', ondelete="cascade"),
    }

dm_offer_history() # }}}


class dm_campaign_proposition(osv.osv): #{{{
    _name = "dm.campaign.proposition"
    _inherits = {'account.analytic.account': 'analytic_account_id'}

    def default_get(self, cr, uid, fields, context=None):
        value = super(dm_campaign_proposition, self).default_get(cr, uid, fields, context)
        if 'camp_id' in context and context['camp_id']:
            campaign = self.pool.get('dm.campaign').browse(cr, uid, context['camp_id'])
            value['date_start'] = campaign.date_start
        return value

    def write(self, cr, uid, ids, vals, context=None):
        if 'camp_id' in vals and vals['camp_id']:
            campaign = self.pool.get('dm.campaign').browse(cr, uid, vals['camp_id'])
            vals['parent_id'] = self.pool.get('account.analytic.account').search(cr, uid, [('id', '=', campaign.analytic_account_id.id)])[0]
            if campaign.date_start:
                vals['date_start'] = campaign.date_start
            else:
                vals['date_start'] = 0
        return super(dm_campaign_proposition, self).write(cr, uid, ids, vals, context)

    def create(self, cr, uid, vals, context={}):
        id = self.pool.get('dm.campaign').browse(cr, uid, vals['camp_id'])
        vals['parent_id'] = self.pool.get('account.analytic.account').search(cr, uid, [('id', '=', id.analytic_account_id.id)])[0]
        if 'date_start' in vals and not vals['date_start']:
            if id.date_start:
                vals['date_start'] = id.date_start
        if 'forwarding_charge' not in vals:
            if id.forwarding_charge:
                vals['forwarding_charge'] = id.forwarding_charge
            elif id.country_id.forwarding_charge:
                vals['forwarding_charge'] = id.country_id.forwarding_charge
        if id.journal_id:
            journal_id = id.journal_id.id
            vals['journal_id'] = journal_id
        return super(dm_campaign_proposition, self).create(cr, uid, vals, context)

    def copy(self, cr, uid, id, default=None, context={}):
        """
        Function to duplicate segments only if 'keep_segments' is set to yes
                                                else not to duplicate segments
        """
        proposition_id = super(dm_campaign_proposition, self).copy(cr, uid, id, default, context=context)
        if 'camp_id' in default and default['camp_id']:
            self.write(cr, uid, proposition_id, {'camp_id': default['camp_id']})

        data = self.browse(cr, uid, proposition_id, context)
        default_name = ' %s (Copy)' % data.name
        super(dm_campaign_proposition, self).write(cr, uid, proposition_id,
                                                    {'name': default_name,
#                                                     'date_start': False,
                                                'initial_proposition_id': id})

        if data.keep_segments == False:
            l = []
            for i in data.segment_ids:
                l.append(i.id)
                self.pool.get('dm.campaign.proposition.segment').unlink(cr, uid, l)
                self.write(cr, uid, proposition_id, {'segment_ids': [(6, 0, [])]})

        # Function to duplicate products only if 'keep_prices' is set to yes else
        #  not to duplicate products
        if data.keep_prices == False:
            l = []
            for i in data.item_ids:
                l.append(i.id)
                self.pool.get('dm.campaign.proposition.item').unlink(cr, uid, l)
                self.write(cr, uid, proposition_id, {'item_ids': [(6, 0, [])]})
        return proposition_id

    def _quantity_wanted_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for propo in self.browse(cr, uid, ids):
            if not propo.segment_ids:
                result[propo.id] = 'No segments defined'
                continue
            qty = 0
            numeric = True
            for segment in propo.segment_ids:
                if segment.all_add_avail:
                    result[propo.id] = 'AAA for a Segment'
                    numeric = False
                    continue
                if not segment.quantity_wanted:
                    result[propo.id] = 'Wanted Quantity missing in a Segment'
                    numeric = False
                    continue
                elif segment.segment_state == 'validated':
                    qty += segment.quantity_wanted
            if numeric:
                result[propo.id] = str(qty)
        return result

    def _quantity_planned_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for propo in self.browse(cr, uid, ids):
            if not propo.segment_ids:
                result[propo.id] = 'No segments defined'
                continue
            qty = 0
            for segment in propo.segment_ids:
                if segment.quantity_planned == 0:
                    result[propo.id] = 'planned Quantity missing in a Segment'
                    continue
                qty += segment.quantity_planned
            result[propo.id] = str(qty)
        return result

    def _quantity_delivered_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for propo in self.browse(cr, uid, ids):
            if not propo.segment_ids:
                result[propo.id] = 'No segments defined'
                continue
            qty = 0
            for segment in propo.segment_ids:
                if segment.quantity_delivered == 0:
                    result[propo.id] = 'Delivered Quantity missing in a Segment'
                    continue
                elif segment.segment_state == 'validated':
                    qty += segment.quantity_delivered
            result[propo.id] = str(qty)
        return result

    def _quantity_usable_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for propo in self.browse(cr, uid, ids):
            if not propo.segment_ids:
                result[propo.id] = 'No segments defined'
                continue
            qty = 0
            for segment in propo.segment_ids:
                if segment.quantity_usable == 0:
                    result[propo.id] = 'Usable Quantity missing in a Segment'
                    continue
                elif segment.segment_state == 'validated':
                    qty += segment.quantity_usable
            result[propo.id] = str(qty)
        return result

    def _quantity_real_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for propo in self.browse(cr, uid, ids):
            if not propo.segment_ids:
                result[propo.id] = 'No segments defined'
                continue
            qty = 0
            for segment in propo.segment_ids:
                if segment.quantity_real == 0:
                    result[propo.id] = 'Real Quantity missing in a Segment'
                    continue
                elif segment.segment_state == 'validated':
                    qty += segment.quantity_real
            result[propo.id] = str(qty)
        return result

    def _default_camp_date(self, cr, uid, context={}):
        if 'date1' in context and context['date1']:
            dd = context['date1']
            return dd
        return []

    _columns = {
        'camp_id': fields.many2one('dm.campaign', 'Campaign',
                                   ondelete = 'cascade', required=True),
        'sale_rate': fields.float('Sale Rate (%)', digits=(16, 2),
                    help='This is the planned sale rate (in percent) for this commercial proposition'),
        'proposition_type': fields.selection([('init', 'Initial'),
                                              ('relaunching', 'Relauching'),
                                               ('split', 'Split')], "Type"),
        'initial_proposition_id': fields.many2one('dm.campaign.proposition',
                                                   'Initial proposition'),
        'segment_ids': fields.one2many('dm.campaign.proposition.segment',
                                       'proposition_id', 'Segment',
                                        ondelete='cascade'),
        'quantity_planned': fields.integer('Planned Quantity',
                             help='The planned quantity is an estimation of the usable quantity of addresses you  will get after delivery, deduplication and cleaning.\n'
                            'This is usually the quantity used to order the manufacturing of the mailings'),
        'quantity_wanted': fields.function(_quantity_wanted_get, string='Wanted Quantity', type="char", size=64, method=True, readonly=True,
                    help='The wanted quantity is the number of addresses you wish to get for that segment.\n'
                            'This is usually the quantity used to order Customers Lists.\n'
                            'The wanted quantity could be AAA for All Addresses Available'),
        'quantity_delivered': fields.function(_quantity_delivered_get, string='Delivered Quantity', type="char", size=64, method=True, readonly=True,
                    help='The delivered quantity is the number of addresses you receive from the broker.'),
        'quantity_usable': fields.function(_quantity_usable_get, string='Usable Quantity', type="char", size=64, method=True, readonly=True,
                    help='The usable quantity is the number of addresses you have after delivery, deduplication and cleaning.'),
        'quantity_real': fields.function(_quantity_real_get, string='Real Quantity', type="char", size=64, method=True, readonly=True,
                    help='The real quantity is the number of addresses you really get in the file.'),
        'starting_mail_price': fields.float('Starting Mail Price', digits=(16, 2)),
        'customer_pricelist_id': fields.many2one('product.pricelist', 'Product Pricelist', required=False),
        'forwarding_charges': fields.float('Forwarding Charges', digits=(16, 2)),
        'notes': fields.text('Notes'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', ondelete='cascade'),
        'item_ids': fields.one2many('dm.campaign.proposition.item', 'proposition_id', 'Catalogue'),
        'journal_id': fields.many2one('account.journal', 'Payment Methods', domain="[('type','=','cash')]"),
        'keep_segments': fields.boolean('Keep Segments'),
        'keep_prices': fields.boolean('Keep Prices At Duplication'),
        'manufacturing_costs': fields.float('Manufacturing Costs', digits=(16, 2)),
        'forwarding_charge': fields.float('Forwarding Charge', digits=(16, 2)),

    }

    _defaults = {
        'proposition_type': lambda *a: 'init',
#        'date_start': _default_camp_date,
        'keep_segments': lambda *a: True,
        'keep_prices': lambda *a: True,
    }

    def onchange_campaign(self, cr, uid, ids, camp_id):
        if camp_id:
            campaign = self.pool.get('dm.campaign').browse(cr, uid, camp_id)
            forwarding_charge = campaign.forwarding_charge or 0.0
            date_start = campaign.date_start or False
            return {'value': {'forwarding_charge': forwarding_charge, 'date_start': date_start}}
        return False

    def _check(self, cr, uid, ids=False, context={}):
        '''
        Function called by the scheduler to create workitem from the segments of propositions.
        '''
        ids = self.search(cr, uid, [('date_start', '=', time.strftime('%Y-%m-%d'))])
        for id in ids:
            res = self.browse(cr, uid, [id])[0]
            offer_step_id = self.pool.get('dm.offer.step').search(cr, uid, [('offer_id', '=', res.camp_id.offer_id.id), ('flow_start', '=', True)])
            if offer_step_id:
                for segment in res.segment_ids:
                    vals = {'step_id': offer_step_id[0], 'segment_id': segment.id}
                    new_id = self.pool.get('dm.offer.step.workitem').create(cr, uid, vals)
        return True

dm_campaign_proposition()#}}}


class dm_customers_list_recruit_origin(osv.osv): #{{{
    _name = "dm.customers_list.recruit_origin"
    _description = "The origin of the adresses of a list"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=16, required=True),
    }

dm_customers_list_recruit_origin()#}}}


class dm_customers_list_type(osv.osv): #{{{
    _name = "dm.customers_list.type"
    _description = "Type of the adress list"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=16, required=True),
    }

dm_customers_list_type()#}}}


class dm_customers_list(osv.osv): #{{{
    _name = "dm.customers_list"
    _description = "A list of addresses proposed by an adresses broker"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context and 'campaign_id' in context and context['campaign_id']:
            campaign_country = self.pool.get('dm.campaign').read(cr,uid,context['campaign_id'],['country_id'])
            if campaign_country.has_key('country_id'):
                cr.execute('select cust_list_id from dm_cust_list_country_rel where country_id=%s' %(campaign_country['country_id'][0]))
                res=cr.fetchall()
                args.append(('id','in',res))
        return super(dm_customers_list, self).search(cr, uid, args, offset, limit, order, context, count)

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=32, required=True),
        'owner_id': fields.many2one('res.partner', 'Owner',
                                    domain=[('category_id', 'ilike', 'Owner')],
                                    context={'category_xml_id': 'cat_owner'}),
        'broker_id': fields.many2one('res.partner', 'Broker',
                                    domain=[('category_id', 'ilike', 'Broker')],
                                    context={'category_xml_id': 'cat_broker'}),
        'country_ids': fields.many2many('res.country',
                                        'dm_cust_list_country_rel',
                                        'cust_list_id', 'country_id',
                                        'Country'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
        'product_id': fields.many2one('product.product', 'Product',
                            domain=[('categ_id', 'ilike', 'Customers List')],
                            context={'category': 'Customers List'},
                            required=True),
        'per_thousand_price': fields.float('Price per Thousand',
                                           digits=(16, 2)),
        'delivery_cost': fields.float('Delivery Cost', digits=(16, 2)),
        'selection_cost': fields.float('Selection Cost Per Thousand',
                                       digits=(16, 2)),
        'broker_cost': fields.float('Broker Cost', digits=(16, 2),
                    help='The amount given to the broker for the list renting'),
        'broker_discount': fields.float('Broker Discount (%)', digits=(16, 2)),
        'other_cost': fields.float('Other Cost', digits=(16, 2)),
        'invoice_base': fields.selection([('net', 'Net Addresses Quantity'),
                                          ('raw', 'Raw Addresses Quantity')],
                                          'Invoicing based on',
                    help='Net or raw quantity on which is based the final invoice depending of the term negotiated with the broker.\n'
                            'Net : Usable quantity after deduplication.\n'
                            'Raw : Delivered quantity.\n' \
                            'Real : Realy used qunatity.'),
        'recruiting_origin_id': fields.many2one('dm.customers_list.recruit_origin',
                                                 'Recruiting Origin',
                    help='Origin of the recruiting of the adresses.'),
        'list_type_id': fields.many2one('dm.customers_list.type', 'Type'),
        'update_frq': fields.integer('Update Frequency'),
        'notes': fields.text('Description'),
        'media_id': fields.many2one('dm.media', 'Media'),
    }

    _defaults = {
        'invoice_base': lambda *a: 'net',
    }

    def copy(self, cr, uid, id, default=None, context=None):
        raw_code = self.browse(cr, uid, id).code
        this_code = re.sub(r' \(Copy\d*?\)', '', raw_code)

        cr.execute("select code from dm_customers_list where code like '%s%%'" % (this_code, ))
        existing_codes = [item[0] for item in cr.fetchall()]

        num = 0
        while True:
            num += 1
            new_code = this_code + ' (Copy%s)' % (num, )
            if new_code not in existing_codes:
                break

        default['code'] = new_code
        return super(dm_customers_list, self).copy(cr, uid, id, default=default, context=context)

    def check_code_unicity(self, cr, uid, ids):
        cust_list_ids = self.search(cr, uid, [('id', 'not in', tuple(ids))])
        cust_list_codes = [cust_list['code'] for cust_list in self.read(cr, uid, cust_list_ids)]
        this_codes = dict([(item['id'], item['code']) for item in self.read(cr, uid, ids, ['code'])])
        for id in ids:
            code = this_codes[id]
            if code and code in cust_list_codes:
                print code
                return False
        return True

    _constraints = [
        (check_code_unicity, 'Error: the code must be unique !', ['code']),
    ]

dm_customers_list()#}}}


class dm_customers_file(osv.osv): #{{{
    _name = "dm.customers_file"
    _description = "A File of addresses"

    _FILE_SOURCES = [
        ('address_id', 'Partner Addresses'),
    ]

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=16, required=True),
        'customers_list_id': fields.many2one('dm.customers_list',
                                              'Customers List'),
        'delivery_date': fields.date('Delivery Date'),
        'address_ids': fields.many2many('res.partner.address',
                                        'dm_cust_file_address_rel',
                                        'cust_file_id', 'address_id',
                                        'Customers File Addresses'),
        'segment_ids': fields.one2many('dm.campaign.proposition.segment',
                                       'customers_file_id', 'Segments',
                                       readonly=True),
        'source': fields.selection(_FILE_SOURCES, 'Source', required=True),
        'note': fields.text('Notes'),
    }
    _defaults = {
        'source': lambda *a: 'address_id',
    }

dm_customers_file()#}}}


class dm_campaign_proposition_segment(osv.osv): #{{{

    _name = "dm.campaign.proposition.segment"
    _inherits = {'account.analytic.account': 'analytic_account_id'}
    _description = "A subset of addresses coming from a customers file"

    def write(self, cr, uid, ids, vals, context=None):
        if 'proposition_id' in vals and vals['proposition_id']:
            proposition_id = self.pool.get('dm.campaign.proposition').browse(cr,
                                                 uid, vals['proposition_id'])
            vals['parent_id'] = self.pool.get('account.analytic.account').search(cr, uid, [('id', '=', proposition_id.analytic_account_id.id)])[0]
        return super(dm_campaign_proposition_segment, self).write(cr, uid, ids,
                                                                 vals, context)

    def create(self, cr, uid, vals, context={}):
        if 'proposition_id' in vals and vals['proposition_id']:
            proposition_id = self.pool.get('dm.campaign.proposition').browse(cr,
                                                    uid, vals['proposition_id'])
            vals['parent_id'] = self.pool.get('account.analytic.account').search(cr, uid, [('id', '=', proposition_id.analytic_account_id.id)])[0]
        return super(dm_campaign_proposition_segment, self).create(cr, uid, vals, context)

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
                                context=None, count=False):
        if context and 'dm_camp_id' in context:
            if not context['dm_camp_id']:
                return []
            res = self.pool.get('dm.campaign').browse(cr, uid,
                                                       context['dm_camp_id'])
            seg_ids = []
            for pro  in res.proposition_ids:
                seg_ids.extend(map(lambda x: x.id, pro.segment_ids))
            return seg_ids
        return super(dm_campaign_proposition_segment, self).search(cr, uid,
                                                        args, offset, limit,
                                                        order, context, count)

    def _quantity_usable_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for segment in self.browse(cr, uid, ids):
            result[segment.id] = segment.quantity_delivered - segment.quantity_dedup_dedup - segment.quantity_cleaned_dedup - segment.quantity_dedup_cleaner - segment.quantity_cleaned_cleaner
        return result

    def _quantity_purged_get(self, cr, uid, ids, name, args, context={}):
        result = {}
        for segment in self.browse(cr, uid, ids):
            result[segment.id] = segment.quantity_delivered - segment.quantity_usable
        return result

##     def _segment_code(self, cr, uid, ids, name, args, context={}):
##         result ={}
##         for id in ids:
##             seg = self.browse(cr, uid, [id])[0]
##             if seg.customers_list_id:
##                 segment_list = self.search(cr, uid, [('customers_list_id', '=',
##                                                 seg.customers_list_id.id)])
##                 i = 1
##                 for s in segment_list:
##                     country_code = seg.customers_list_id.country_id.code or ''
##                     cust_list_code =  seg.customers_list_id.code
##                     seq = '%%0%sd' % 2 % i
##                     code='-'.join([country_code[:3], cust_list_code[:3],
##                                                                   seq[:4]])
##                     result[s]=code
##                     i +=1
##             elif seg.customers_file_id:
##                 segment_list = self.search(cr, uid,
##                       [('customers_file_id', '=', seg.customers_file_id.id)])
##                 i = 1
##                 for s in segment_list:
##                     cust_file_code =  seg.customers_file_id.code
##                     seq = '%%0%sd' % 2 % i
##                     code='-'.join([cust_file_code[:3], seq[:4]])
##                     result[s]=code
##                     i +=1
##             else:
##                 result[seg.id]=seg.type_src+'%d'%id
##         return result
    def onchange_list(self, cr, uid, ids, customers_list, start_census,
                                                                end_census):
        if customers_list:
            list = self.pool.get('dm.customers_list').browse(cr, uid,
                                                        [customers_list])[0]
            if start_census == 0 and end_census == 0:
                file_name = list.name
            else:
                file_name = list.name + '-' + str(start_census) + '/' + \
                                                                str(end_census)
            return {'value': {'name': file_name}}
        return False

    def copy(self, cr, uid, id, default=None, context={}):
        if not default:
            default = {}
        segment_id = self.browse(cr, uid, id)
        if not default.get('name', False):
            default['name'] = segment_id.name + ' (Copy)'
        seg_copy_id = super(dm_campaign_proposition_segment, self).copy(cr, uid,
                                                         id, default, context)
        return seg_copy_id

    _columns = {
        'campaign_id': fields.related('proposition_id', 'camp_id',
                                      type='many2one', relation='dm.campaign',
                                      string='Campaign'),
        'country_id': fields.many2one('res.country', 'Country'),
        'proposition_id': fields.many2one('dm.campaign.proposition',
                                          'Proposition', ondelete='cascade'),
        'type_src': fields.selection([('internal', 'Internal'),
                                      ('external', 'External')], 'Type'),
        'customers_list_id': fields.many2one('dm.customers_list',
                                             'Customers List'),
        'customers_file_id': fields.many2one('dm.customers_file',
                                             'Customers File'),
        'quantity_real': fields.integer('Real Quantity',
                   help='The real quantity is the number of addresses that are really in the customers file (by counting).'),
        'quantity_planned': fields.integer('planned Quantity',
                    help='The planned quantity is an estimation of the usable quantity of addresses you  will get after delivery, deduplication and cleaning.\n This is usually the quantity used to order the manufacturing of the mailings'),
        'quantity_wanted': fields.integer('Wanted Quantity',
                    help='The wanted quantity is the number of addresses you wish to get for that segment.\n This is usually the quantity used to order Customers Lists.\n'
                            'The wanted quantity could be AAA for All Addresses Available.'),
        'quantity_delivered': fields.integer('Delivered Quantity',
                help = 'The delivered quantity is the number of addresses you receive from the broker.'),
        'quantity_dedup_dedup': fields.integer('Deduplication Quantity',
                    help='The quantity of duplicated addresses removed by the deduplicator.'),
        'quantity_dedup_cleaner': fields.integer('Deduplication Quantity',
                    help='The quantity of duplicated addresses removed by the cleaner.'),
        'quantity_cleaned_dedup': fields.integer('Cleaned Quantity',
                    help='The quantity of wrong addresses removed by the deduplicator.'),
        'quantity_cleaned_cleaner': fields.integer('Cleaned Quantity',
                    help='The quantity of wrong addresses removed by the cleaner.'),
        'quantity_usable': fields.function(_quantity_usable_get,
                                           string='Usable Quantity',
                                           type="integer",
                                           method=True,
                                           readonly=True,
                    help='The usable quantity is the number of addresses you have after delivery, deduplication and cleaning.'),
        'quantity_purged': fields.function(_quantity_purged_get,
                                           string='Purged Quantity',
                                           type="integer",
                                           method=True,
                                           readonly=True,
                    help='The purged quantity is the number of addresses removed from deduplication and cleaning.'),
        'all_add_avail': fields.boolean('All Adresses Available',
                    help='Used to order all adresses available in the customers list based on the segmentation criteria'),
        'split_id': fields.many2one('dm.campaign.proposition.segment', 'Split'),
        'start_census': fields.integer('Start Census',
                        help='The recency is the time since the latest purchase.\n For example: A 0-30 recency means all the customers that have purchased in the last 30 days.'),
        'end_census': fields.integer('End Census'),
        'deduplication_level': fields.integer('Deduplication Level',
                    help='The deduplication level defines the order in which the deduplication takes place.'),
        'reuse_id': fields.many2one('dm.campaign.proposition.segment', 'Reuse'),
        'analytic_account_id': fields.many2one('account.analytic.account',
                                               'Analytic Account',
                                               ondelete='cascade'),
        'note': fields.text('Notes'),
        'segmentation_criteria': fields.text('Segmentation Criteria'),
        'type_census': fields.selection([('minutes', 'Minutes'),
                                         ('hours', 'Hours'),
                                         ('days', 'Days'),
                                         ('months', 'Months')],
                                         'Census Type'),
        'segment_state': fields.selection([('validated','Validated'),
                                           ('rejected','Rejected'),
                                           ('canceled','Canceled')],
                                           'Status'),
    }
    _order = 'deduplication_level'
    _defaults = {
        'all_add_avail': lambda *a: True,
        'type_census': lambda *a: 'days',
        'type_src': lambda *a: 'internal',
        'segment_state': lambda *a: 'validated',
    }

dm_campaign_proposition_segment()#}}}

AVAILABLE_ITEM_TYPES = [ # {{{
    ('main', 'Main Item'),
    ('standart', 'Standart Item'),
] # }}}


class dm_campaign_proposition_item(osv.osv): #{{{
    _name = "dm.campaign.proposition.item"
    _rec_name = 'product_id'
    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True,
                                      context={'flag': True}),
        'qty_planned': fields.integer('Planned Quantity'),
        'qty_real': fields.integer('Real Quantity'),
        'price': fields.float('Sale Price'),
        'proposition_id': fields.many2one('dm.campaign.proposition',
                                          'Commercial Proposition'),
        'item_type': fields.selection(AVAILABLE_ITEM_TYPES,
                                      'Product Type', size=64),
        'offer_step_id': fields.many2one('dm.offer.step', 'Offer Step Name'),
        'notes': fields.text('Notes'),
        'forecasted_yield': fields.float('Forecasted Yield'),
    }

dm_campaign_proposition_item()#}}}


class dm_campaign_manufacturing_cost(osv.osv): #{{{
    _name = 'dm.campaign.manufacturing_cost'
    _columns = {
        'name': fields.char('Description', size=64, required=True),
        'amount': fields.float('Amount', digits=(16, 2)),
        'campaign_id': fields.many2one('dm.campaign', 'Campaign'),
    }

dm_campaign_manufacturing_cost()#}}}


class dm_mail_service_type(osv.osv): # {{{
    _name = "dm.mail_service.type"
    _columns = {
        'name': fields.char('Name', size=64),
        'code': fields.char('Code', size=64),
    }

dm_mail_service_type() # }}}


class dm_mail_service(osv.osv): # {{{
    _name = "dm.mail_service"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'partner_id': fields.many2one('res.partner', 'Partner',
                            domain=[('category_id', 'ilike', 'Mail Service')],
                            context={'category_xml_id': 'cat_mail_service'}),
        'media_id': fields.many2one('dm.media', 'Media'),
        'time_mode': fields.selection([('hour', 'Fixed Hour'),
                                       ('date', 'Fixed Date'),
                                       ('interval', 'Interval')],
                                       'Time Mode'),
        'action_hour': fields.float('Hours'),
        'action_date': fields.datetime('Date'),
        'action_interval': fields.integer('Interval'),
        'unit_interval': fields.selection([('minutes', 'Minutes'),
                                            ('hours', 'Hours'),
                                            ('days', 'Days'),
                                            ('weeks', 'Weeks'),
                                             ('months', 'Months')],
                                             'Interval Unit'),
        'default_for_media': fields.boolean('Default Mail Service for Media'),
        'action_id': fields.many2one('ir.actions.server', 'Server Action',
                                     domain=[('model_id.model','=', 'dm.campaign.document')],),
        'type_id': fields.many2one('dm.mail_service.type', 'Type',
                                                    ondelete="cascade"),
        'hosted_image_use': fields.boolean('Hosted Image'),
        'smtp_server_id': fields.many2one('email.smtpclient',
                                          'SMTP Server', ondelete="cascade"),
        'service_type': fields.char('Type Code', size=64),
        'store_document': fields.boolean('Store Document'),
    }

    def check_unique_mail_service(self, cr, uid, ids, media_id,
                                    default_for_media):
        if default_for_media:
            res = self.search(cr, uid, [('media_id', '=', media_id),
                                        ('default_for_media', '=', True)])
            if res and (ids and (res in ids) or True):
                return {'value': {'default_for_media': False}}
        else:
            return True

    def on_change_service_type(self, cr, uid, ids, type_id):
        res = {'value': {}}
        if type_id:
            service_type = self.pool.get('dm.mail_service.type').read(cr, uid, [type_id])[0]
            res['value'] = {'service_type': service_type['code']}
        return res

dm_mail_service() # }}}


class dm_campaign_mail_service(osv.osv): # {{{
    _name = "dm.campaign.mail_service"
    _rec_name = 'mail_service_id'
    _columns = {
        'mail_service_id': fields.many2one('dm.mail_service', 'Mail Service'),
        'campaign_id': fields.many2one('dm.campaign', 'Campaign'),
        'offer_step_id': fields.many2one('dm.offer.step', 'Offer Step'),
    }

dm_campaign_mail_service() # }}}

