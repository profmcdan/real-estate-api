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


class Mutation(graphene.ObjectType):
    create_agent = CreateAgent.Field()


class Query(graphene.ObjectType):
    agents = graphene.List(AgentType, search=graphene.String(
    ), first=graphene.Int(), skip=graphene.Int())

    def resolve_agents(self, info, search=None, first=None, skip=None, **kwargs):
        qs = Agent.objects.all()
        return resolve_with_filter_and_pagination(qs, search, first, skip)
