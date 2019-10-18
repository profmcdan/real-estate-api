import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
# from graphene_file_upload.scalars import Upload
from django.db.models import Q
from users.schema import UserType
from core.models import Agent, Apartment, ApartmentPicture


def resolve_with_filter_and_pagination(queryset, search, first, skip):
    if search:
        filters = (
            Q(company_name__icontains=search) | Q(address__icontains=search)
        )
        queryset = queryset.filter(filters)
    if skip:
        queryset = queryset[skip:]
    if first:
        queryset = queryset[:first]
    return queryset


class AgentType(DjangoObjectType):
    class Meta:
        model = Agent


class ApartmentType(DjangoObjectType):
    class Meta:
        model = Apartment


class ApartmentPictureType(DjangoObjectType):
    class Meta:
        model = ApartmentPicture


class CreateAgent(graphene.Mutation):
    """ Update the profile of a logged in Agent  """
    id = graphene.Int()
    user = graphene.Field(UserType)
    company_name = graphene.String()
    address = graphene.String()
    phone = graphene.String()
    whatsapp_number = graphene.String()
    picture = graphene.String()

    class Arguments:
        company_name = graphene.String()
        address = graphene.String()
        phone = graphene.String()
        whatsapp_number = graphene.String()
        picture = graphene.String()

    def mutate(self, info, **input):
        user = info.context.user or None
        if user.is_anonymous:
            raise GraphQLError('You must be authenticated')
        agent = Agent.objects.filter(user=user).first()
        if agent:
            Agent.objects.filter(user=user).update(
                company_name=input.get('company_name'),
                address=input.get('address'), phone=input.get('phone'),
                whatsapp_number=input.get('whatsapp_number'),
                picture=input.get('picture')
            )
            agent.refresh_from_db()
        else:
            agent = Agent(user=user, company_name=input.get('company_name'),
                          address=input.get('address'), phone=input.get('phone'),
                          whatsapp_number=input.get('whatsapp_number'),
                          picture=input.get('picture'))
            agent.save()
        return CreateAgent(
            id=agent.id, user=agent.user, company_name=agent.company_name,
            address=agent.address, phone=agent.phone, picture=agent.picture,
            whatsapp_number=agent.whatsapp_number
        )


class CreateApartment(graphene.Mutation):
    id = graphene.Int()
    agent = graphene.Field(AgentType)
    title = graphene.String(required=True)
    address = graphene.String(required=True)
    features = graphene.String(required=True)

    class Arguments:
        title = graphene.String(required=True)
        address = graphene.String(required=True)
        features = graphene.String(required=True)

    def mutate(self, info, **request_data):
        user = info.context.user or None
        if user.is_anonymous:
            raise GraphQLError('Authentication credentials not provided')
        agent = Agent.objects.filter(user=user).first()
        if not agent:
            raise GraphQLError('Agent profile does not exists')
        title = request_data.get('title')
        address = request_data.get('address')
        features = request_data.get('features')
        apartment = Apartment(agent=agent, address=address,
                              features=features, title=title)
        apartment.save()
        return CreateApartment(id=apartment.id, agent=apartment.agent,
                               address=apartment.address, features=apartment.features,
                               title=apartment.title)


class AddApartmentImage(graphene.Mutation):
    id = graphene.Int()
    apartment = graphene.Field(ApartmentType)
    image = graphene.String()

    class Arguments:
        apartmentId = graphene.Int()
        image = graphene.String()

    def mutate(self, info, **request_data):
        user = info.context.user or None
        if user.is_anonymous:
            raise GraphQLError('Authentication credentials not provided')
        apartmentId = request_data.get('apartmentId')
        image = request_data.get('image')
        apartment = Apartment.objects.filter(id=apartmentId).first()
        if not apartment:
            raise GraphQLError('Appartment with that Id does not exist')
        if apartment.agent.user != user:
            raise GraphQLError(
                'This apartment does not belong to you, hence you cant edit it')
        apartmentPicture = ApartmentPicture(apartment=apartment, image=image)
        apartmentPicture.save()
        return AddApartmentImage(id=apartmentPicture.id, apartment=apartment, image=image)


class Mutation(graphene.ObjectType):
    create_agent = CreateAgent.Field()
    create_apartment = CreateApartment.Field()
    add_apartment_image = AddApartmentImage.Field()


class Query(graphene.ObjectType):
    agents = graphene.List(AgentType, search=graphene.String(),
                           first=graphene.Int(), skip=graphene.Int())
    apartments = graphene.List(ApartmentType, apartmentId=graphene.Int(),
                               search=graphene.String(), first=graphene.Int(),
                               skip=graphene.Int())

    def resolve_agents(self, info, search=None, first=None, skip=None, **kwargs):
        """ Returns a paginated list of Agents """
        qs = Agent.objects.all()
        return resolve_with_filter_and_pagination(qs, search, first, skip)

    def resolve_apartments(self, info,  apartmentId=None, search=None, first=None, skip=None, **kwargs):
        """ Returns a paginated list of Apartments """
        qs = Apartment.objects.all()
        if apartmentId:
            apartment = qs.filter(id=apartmentId)
            if not apartment:
                raise GraphQLError('Apartment not found')
            return apartment
        return resolve_with_filter_and_pagination(qs, search, first, skip)
